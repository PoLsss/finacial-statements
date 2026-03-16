from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pathlib import Path
from tenacity import retry, wait_exponential
import os
import json
from langfuse.openai import OpenAI
from langfuse import observe
from backend.implementations.question_classifier import get_rag_strategy
from backend.implementations.agent_tools import search, analyze, verify
from backend.implementations.mongodb_manager import get_mongodb_manager

load_dotenv(override=True)

# Configuration
MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

wait = wait_exponential(multiplier=1, min=10, max=240)

# Initialize OpenAI client
openai = OpenAI()

# Initialize MongoDB manager
try:
    mongo = get_mongodb_manager()
    db_initialized = mongo.get_all_embeddings_count() > 0
except Exception as e:
    print(f"Warning: Could not connect to MongoDB: {e}")
    mongo = None
    db_initialized = False

RETRIEVAL_K = 10
FINAL_K = 8

SYSTEM_PROMPT = """
You are an expert financial analyst and advisor.
Your role is to provide comprehensive financial insights and analysis to users asking about financial reports and data.

**Guidelines for your responses:**

1. **Direct Answer**: Start with a clear, concise answer to the user's question.

2. **Detailed Analysis**: Explain WHY this answer is correct by:
   - Referencing specific figures, dates, and sources from the provided context
   - Breaking down the financial logic and reasoning
   - Highlighting key financial metrics or ratios relevant to the question

3. **Calculations & Statistics**: When applicable:
   - **MANDATORY**: When comparing figures across periods, ALWAYS calculate and explicitly state the percentage change (increase or decrease)
   - Compare current figures to equivalent periods (year-over-year, quarter-over-quarter)
   - Show both old and new values with the exact percentage change percentage
   - Example format: "Operating cash flow declined sharply from 4,117,726,957,514 VND in the first 9 months of 2024 to 2,056,436,501,352 VND in the same period of 2025, representing a decrease of 49.23%"
   - Show calculation steps for growth rates and trends
   - Perform and show basic calculations (percentages, growth rates, averages, trends)
   - Identify patterns, anomalies, or significant movements in the data
   - Use proper financial terminology and precision

4. **Structured Presentation**: Format your response for clarity:
   - Use numbers and bullet points where helpful
   - Organize by categories or time periods
   - Include supporting data from the knowledge base
   - Highlight percentage changes prominently when comparing periods

5. **Professional Tone**: Maintain an expert, confident tone while being accessible to the user.

6. **Transparency**: If the provided context is insufficient or if certain data is missing, explicitly state this.

7. **Do Not Speculate**: Only use information from the provided financial reports. If you cannot answer based on the context, say so clearly.

8. Allway reponse in Vietnamese.

**Available Context from Financial Reports Knowledge Base:**
{context}

Now, please analyze the user's question thoroughly and provide a comprehensive, well-reasoned financial analysis, with mandatory percentage change calculations when comparing figures across different periods.
"""


class Result(BaseModel):
    page_content: str
    metadata: dict


@observe(name="rerank_chunks", as_type="chain")
@retry(wait=wait)
def rerank(question, chunks):
    """Rerank chunks by relevance using LLM."""
    system_prompt = """
    You are a financial reports document re-ranker.
    You are provided with a question and a list of relevant chunks of text from a knowledge base.
    The chunks are provided in the order they were retrieved; this should be approximately ordered by relevance, but you may be able to improve on that.
    You must rank order the provided chunks by relevance to the question, with the most relevant chunk first.
    Reply ONLY with a JSON object like {"order": [1, 3, 2]} with chunk ids reordered, nothing else.
    """
    user_prompt = f"The user has asked the following question:\n\n{question}\n\nOrder all the chunks of text by relevance to the question, from most relevant to least relevant. Include all the chunk ids you are provided with, reranked.\n\n"
    user_prompt += "Here are the chunks:\n\n"
    for index, chunk in enumerate(chunks):
        content_preview = chunk['page_content']
        user_prompt += f"# CHUNK ID: {index + 1}:\n\n{content_preview}...\n\n"
    user_prompt += 'Reply ONLY with JSON like {"order": [1, 2, 3]}, nothing else.'
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = openai.chat.completions.create(model=MODEL, messages=messages)
        reply = response.choices[0].message.content.strip()

        data = json.loads(reply)
        order = data.get("order", list(range(1, len(chunks) + 1)))
        result = [chunks[i - 1] for i in order if i <= len(chunks)]
        return result
    except Exception as e:
        print(f"Error in rerank: {e}")
        return chunks


def make_rag_messages(question, history, chunks):
    """Create RAG messages with context from chunks."""
    context_parts = []
    for chunk in chunks:
        source = chunk.get('metadata', {}).get('source', 'Unknown')
        page = chunk.get('metadata', {}).get('page_number', chunk.get('metadata', {}).get('page_index', '?'))
        content = chunk.get('page_content', chunk.get('text', ''))
        context_parts.append(f"Extract from {source} (Page {page}):\n{content}")

    context = "\n\n".join(context_parts)
    system_prompt = SYSTEM_PROMPT.format(context=context)
    return (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": question}]
    )


@observe(name="rewrite-query", as_type="chain")
@retry(wait=wait)
def rewrite_query(question, history=[]):
    """Rewrite the user's question to be more specific for knowledge base search."""
    if not question or not isinstance(question, str) or len(question.strip()) == 0:
        return question

    if not history or len(history) == 0:
        print("First question - skipping query rewriting")
        return question

    try:
        print(f"Rewriting query with conversation context (history: {len(history)} messages)...")

        message = f"""
            You are in a conversation with a user, answering questions about financial reports.
            You are about to look up information in a Knowledge Base to answer the user's question.

            This is the history of your conversation so far with the user:
            {history}

            And this is the user's current question:
            {question}

            Respond ONLY with a short, refined question that you will use to search the Knowledge Base.
            Focus on key financial terms and metrics. Make it clear and specific based on the conversation context.
            Nothing else, just the refined question.
                    """

        response = openai.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": message}]
        )
        result = response.choices[0].message.content.strip()

        if result and isinstance(result, str) and len(result.strip()) > 0:
            print(f"Original: {question[:60]}...")
            print(f"Rewritten: {result[:60]}...")
            return result.strip()

        return question

    except Exception as e:
        print(f"Error in rewrite_query: {e}")
        return question


def merge_chunks(chunks, reranked):
    """Merge two lists of chunks, avoiding duplicates."""
    merged = chunks[:]
    existing = [chunk['page_content'] for chunk in chunks]
    for chunk in reranked:
        if chunk['page_content'] not in existing:
            merged.append(chunk)
    return merged


@observe(name="embedding_and_retrieval", as_type="retriever")
def fetch_context_unranked(question):
    """Fetch context from MongoDB using embedding similarity."""
    if mongo is None:
        print("MongoDB not initialized. Please run the pipeline first.")
        return []

    if not question or not isinstance(question, str) or len(question.strip()) == 0:
        return []

    try:
        question_str = question.strip()
        print(f"Fetching context for: {question_str[:50]}...")

        query_embedding = openai.embeddings.create(
            model=embedding_model,
            input=[question_str]
        ).data[0].embedding

        results = mongo.query_by_embedding(
            query_embedding=query_embedding,
            n_results=RETRIEVAL_K,
        )

        chunks = []
        for doc in results:
            chunks.append({
                "page_content": doc["text"],
                "metadata": doc.get("metadata", {}),
                "similarity": doc.get("similarity", 0.0),
            })

        print(f"Retrieved {len(chunks)} chunks")
        return chunks
    except Exception as e:
        print(f"Error fetching context: {e}")
        return []


@observe(name="fetch_context", as_type="chain")
def fetch_context(original_question, history=[], retrieval_k=None):
    """Fetch and rerank context for a question."""
    try:
        if retrieval_k is None:
            retrieval_k = RETRIEVAL_K

        if history and len(history) > 0:
            try:
                rewritten_question = rewrite_query(original_question, history)
            except Exception as e:
                print(f"Error rewriting query: {e}")
                rewritten_question = original_question
        else:
            rewritten_question = original_question

        if not rewritten_question or not isinstance(rewritten_question, str) or len(rewritten_question.strip()) == 0:
            rewritten_question = original_question

        ori_chunks = fetch_context_unranked(original_question)

        if rewritten_question.strip() != original_question.strip():
            try:
                rewrite_chunks = fetch_context_unranked(rewritten_question)
                chunks = merge_chunks(ori_chunks, rewrite_chunks)
                print(f"Merged chunks from original ({len(ori_chunks)}) and rewritten ({len(rewrite_chunks)}) queries")
            except Exception as e:
                print(f"Error fetching rewritten chunks: {e}")
                chunks = ori_chunks
        else:
            chunks = ori_chunks

        if chunks:
            try:
                print(f"Reranking {len(chunks)} chunks by relevance...")
                reranked = rerank(original_question, chunks)
                result = reranked[:FINAL_K]
                print(f"Returning top {len(result)} reranked chunks")
                return result
            except Exception as e:
                print(f"Error reranking chunks: {e}")
                result = chunks[:retrieval_k]
                return result
        else:
            return []
    except Exception as e:
        print(f"Error in fetch_context: {e}")
        import traceback
        traceback.print_exc()
        return []


@observe(name="rag_pipeline", as_type="chain")
@retry(wait=wait)
def answer_question(question: str, history: list[dict] = []) -> tuple[str, list, dict]:
    """Answer a question using intelligent RAG routing."""
    if mongo is None or not db_initialized:
        return "Error: Knowledge base not initialized. Please run the pipeline first.", [], {}

    try:
        question = str(question).strip() if question else ""

        if not question:
            return "Error: Please enter a question", [], {}

        if not isinstance(history, list):
            history = []

        try:
            strategy = get_rag_strategy(question)
            routing_metadata = {
                "complexity_level": strategy.get("complexity_level", "unknown"),
                "complexity_score": strategy.get("complexity_score", 0),
                "reasoning": strategy.get("reasoning", ""),
                "strategy": strategy.get("strategy", "unknown"),
            }
        except Exception as e:
            print(f"Warning: Question classification failed, using default strategy: {e}")
            strategy = {
                "use_reranking": True,
                "retrieval_k": RETRIEVAL_K,
                "complexity_level": "unknown",
                "complexity_score": 0.5,
                "strategy": "unknown",
            }
            routing_metadata = {"complexity_level": "unknown", "complexity_score": 0.5}

        chunks = fetch_context(
            question,
            history,
            retrieval_k=strategy.get("retrieval_k", RETRIEVAL_K)
        )

        if not chunks or not isinstance(chunks, list):
            chunks = []

        messages = make_rag_messages(question, history, chunks)
        response = openai.chat.completions.create(model=MODEL, messages=messages)
        answer = response.choices[0].message.content

        return answer, chunks, routing_metadata
    except Exception as e:
        print(f"Error in answer_question: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", [], {"error": str(e)}


@observe(name="agent_rag_pipeline", as_type="chain")
def answer_with_agent(question: str, history: list[dict] = []) -> tuple[str, list, dict]:
    """Answer complex questions using agent tools (search, analyze, verify)."""
    if mongo is None or not db_initialized:
        return "Error: Knowledge base not initialized. Please run the pipeline first.", [], {}

    try:
        question = str(question).strip() if question else ""
        if not question:
            return "Error: Please enter a question", [], {}

        if not isinstance(history, list):
            history = []

        search_query = question
        if history and len(history) > 0:
            try:
                print(f"Agent Step 0: Rewriting query with conversation context...")
                search_query = rewrite_query(question, history)
            except Exception as e:
                print(f"Error in query rewriting: {e}")
                search_query = question

        print(f"Agent Step 1: Searching for information...")
        search_result = search(search_query, n_results=10)

        if not search_result.chunks:
            return "I couldn't find relevant information to answer your question.", [], {
                "agent_steps": ["search"],
                "error": "No search results"
            }

        print(f"Agent Step 2: Reranking results by relevance...")
        try:
            search_chunks_for_rerank = [
                {
                    "page_content": chunk.get("text", chunk.get("page_content", "")),
                    "metadata": chunk.get("metadata", {})
                }
                for chunk in search_result.chunks
            ]
            reranked_chunks = rerank(question, search_chunks_for_rerank)
            chunks_for_analysis = reranked_chunks[:8]
            print(f"   Using top {len(chunks_for_analysis)} reranked chunks")
        except Exception as e:
            print(f"   Reranking failed, using original search results: {e}")
            chunks_for_analysis = search_result.chunks[:8]

        print(f"Agent Step 3: Analyzing information...")

        analysis_type = "general"
        question_lower = question.lower()
        if any(word in question_lower for word in ["trend", "over time", "trajectory", "pattern"]):
            analysis_type = "trend"
        elif any(word in question_lower for word in ["compare", "difference", "versus", "vs"]):
            analysis_type = "comparative"
        elif any(word in question_lower for word in ["why", "cause", "reason", "impact", "affect"]):
            analysis_type = "impact"

        analysis_result = analyze(
            question=question,
            context_chunks=chunks_for_analysis,
            analysis_type=analysis_type
        )

        print(f"Agent Step 4: Generating comprehensive answer...")

        answer_parts = []
        answer_parts.append(analysis_result.analysis)

        if analysis_result.insights:
            answer_parts.append("\n\n**Key Insights:**")
            for i, insight in enumerate(analysis_result.insights[:3], 1):
                answer_parts.append(f"{i}. {insight}")

        if analysis_result.sources_used:
            answer_parts.append(f"\n\n**Sources:** {', '.join(set(analysis_result.sources_used))}")

        final_answer = "\n".join(answer_parts)

        workflow_steps = []
        if history and len(history) > 0:
            workflow_steps.append("rewrite")
        workflow_steps.extend(["search", "rerank", "analyze", "answer"])

        agent_metadata = {
            "agent_mode": True,
            "query_rewritten": (history and len(history) > 0 and search_query != question),
            "analysis_type": analysis_type,
            "search_results": search_result.num_results,
            "search_confidence": search_result.confidence,
            "analysis_confidence": analysis_result.confidence,
            "insights_count": len(analysis_result.insights),
            "sources": analysis_result.sources_used,
            "agent_steps": workflow_steps,
        }

        return final_answer, search_result.chunks, agent_metadata

    except Exception as e:
        print(f"Error in agent answer: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", [], {"error": str(e), "agent_mode": True}


@observe(name="hybrid_rag_pipeline", as_type="chain")
@retry(wait=wait)
def answer_question_hybrid(question: str, history: list[dict] = [], use_agent: bool = None) -> tuple[str, list, dict]:
    """Hybrid RAG: Routes between simple RAG and agent-based RAG based on complexity."""
    if mongo is None or not db_initialized:
        return "Error: Knowledge base not initialized. Please run the pipeline first.", [], {}

    try:
        if use_agent is None:
            try:
                strategy = get_rag_strategy(question)
                complexity_score = strategy.get("complexity_score", 0.5)
                complexity_level = strategy.get("complexity_level", "medium")
                reasoning = strategy.get("reasoning", "")

                try:
                    USE_AGENT_MODE_SCORE = float(os.getenv("USE_AGENT_MODE", "0.7"))
                except ValueError:
                    USE_AGENT_MODE_SCORE = 0.7

                use_agent_mode = complexity_score >= USE_AGENT_MODE_SCORE

                routing_metadata = {
                    "complexity_level": complexity_level,
                    "complexity_score": complexity_score,
                    "routing_decision": "agent" if use_agent_mode else "simple",
                    "reasoning": reasoning,
                    "threshold": USE_AGENT_MODE_SCORE,
                }

                print(f"Question classified as '{complexity_level}' (score: {complexity_score:.2f})")
                print(f"   Threshold for agent: {USE_AGENT_MODE_SCORE}")
                print(f"   Decision: {'Agent mode' if use_agent_mode else 'Simple mode'}")

            except Exception as classify_error:
                print(f"Question classification failed: {classify_error}")
                print(f"   Falling back to simple RAG mode")
                use_agent_mode = False
                routing_metadata = {
                    "complexity_level": "unknown",
                    "complexity_score": 0.5,
                    "routing_decision": "simple",
                    "reasoning": f"Classification error: {str(classify_error)}",
                    "fallback": True,
                }
        else:
            use_agent_mode = use_agent
            routing_metadata = {
                "routing_decision": "agent" if use_agent else "simple",
                "forced": True,
            }

        if use_agent_mode:
            print(f"Using Agent RAG (multi-step reasoning)...")
            answer, chunks, agent_metadata = answer_with_agent(question, history)
            final_metadata = {**routing_metadata, **agent_metadata}
            return answer, chunks, final_metadata
        else:
            print(f"Using Simple RAG (fast path)...")
            answer, chunks, simple_metadata = answer_question(question, history)
            final_metadata = {**routing_metadata, **simple_metadata}
            return answer, chunks, final_metadata

    except Exception as e:
        print(f"Error in hybrid answer: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", [], {"error": str(e)}

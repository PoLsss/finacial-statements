# """
# Agent-based answer function integration patch.
# This will be appended to answers.py
# """

# @observe(name="agent_rag_pipeline", as_type="chain")
# def answer_with_agent(question: str, history: list[dict] = []) -> tuple[str, list, dict]:
#     """
#     Answer complex questions using agent tools (search, analyze, verify).
    
#     This function uses a multi-step reasoning approach:
#     1. Search for relevant information
#     2. Analyze the findings
#     3. Verify key claims (optional)
#     4. Generate comprehensive answer
    
#     Args:
#         question: The user's question
#         history: Conversation history
        
#     Returns:
#         tuple: (answer, chunks, metadata)
#     """
#     if collection is None:
#         return "Error: Knowledge base not initialized. Please run the pipeline first.", [], {}
    
#     try:
#         # Validate inputs
#         question = str(question).strip() if question else ""
#         if not question:
#             return "Error: Please enter a question", [], {}
        
#         if not isinstance(history, list):
#             history = []
        
#         # Step 1: Search for relevant information
#         print(f"🔍 Agent Step 1: Searching for information...")
#         search_result = search(question, n_results=10)
        
#         if not search_result.chunks:
#             return "I couldn't find relevant information to answer your question.", [], {
#                 "agent_steps": ["search"],
#                 "error": "No search results"
#             }
        
#         # Step 2: Analyze the information
#         print(f"🧠 Agent Step 2: Analyzing information...")
        
#         # Determine analysis type based on question
#         analysis_type = "general"
#         question_lower = question.lower()
#         if any(word in question_lower for word in ["trend", "over time", "trajectory", "pattern"]):
#             analysis_type = "trend"
#         elif any(word in question_lower for word in ["compare", "difference", "versus", "vs"]):
#             analysis_type = "comparative"
#         elif any(word in question_lower for word in ["why", "cause", "reason", "impact", "affect"]):
#             analysis_type = "impact"
        
#         analysis_result = analyze(
#             question=question,
#             context_chunks=search_result.chunks,
#             analysis_type=analysis_type
#         )
        
#         # Step 3: Build comprehensive answer
#         print(f"📝 Agent Step 3: Generating answer...")
        
#         # Combine analysis with additional context if needed
#         answer_parts = []
        
#         # Main analysis
#         answer_parts.append(analysis_result.analysis)
        
#         # Add key insights if available
#         if analysis_result.insights:
#             answer_parts.append("\n\n**Key Insights:**")
#             for i, insight in enumerate(analysis_result.insights[:3], 1):
#                 answer_parts.append(f"{i}. {insight}")
        
#         # Add sources
#         if analysis_result.sources_used:
#             answer_parts.append(f"\n\n**Sources:** {', '.join(set(analysis_result.sources_used))}")
        
#         final_answer = "\n".join(answer_parts)
        
#         # Prepare metadata
#         agent_metadata = {
#             "agent_mode": True,
#             "analysis_type": analysis_type,
#             "search_results": search_result.num_results,
#             "search_confidence": search_result.confidence,
#             "analysis_confidence": analysis_result.confidence,
#             "insights_count": len(analysis_result.insights),
#             "sources": analysis_result.sources_used,
#             "agent_steps": ["search", "analyze", "answer"],
#         }
        
#         return final_answer, search_result.chunks, agent_metadata
        
#     except Exception as e:
#         print(f"Error in agent answer: {e}")
#         import traceback
#         traceback.print_exc()
        
#         return f"Error: {str(e)}", [], {"error": str(e), "agent_mode": True}


# @observe(name="hybrid_rag_pipeline", as_type="chain")
# @retry(wait=wait)
# def answer_question_hybrid(question: str, history: list[dict] = [], use_agent: bool = None) -> tuple[str, list, dict]:
#     """
#     Hybrid RAG: Routes between simple RAG and agent-based RAG based on complexity.
    
#     Args:
#         question: The user's question
#         history: Conversation history
#         use_agent: Force agent mode (True) or simple mode (False). If None, auto-detect.
        
#     Returns:
#         tuple: (answer, chunks, metadata)
#     """
#     if collection is None:
#         return "Error: Knowledge base not initialized. Please run the pipeline first.", [], {}
    
#     try:
#         # Classify question if not forced
#         if use_agent is None:
#             strategy = get_rag_strategy(question)
            
#             # Use agent for very complex questions (score >= 0.7)
#             use_agent_mode = strategy.get("complexity_score", 0) >= 0.7
            
#             routing_metadata = {
#                 "complexity_level": strategy.get("complexity_level", "unknown"),
#                 "complexity_score": strategy.get("complexity_score", 0),
#                 "routing_decision": "agent" if use_agent_mode else "simple",
#                 "reasoning": strategy.get("reasoning", ""),
#             }
#         else:
#             use_agent_mode = use_agent
#             routing_metadata = {
#                 "routing_decision": "agent" if use_agent else "simple",
#                 "forced": True,
#             }
        
#         # Route to appropriate pipeline
#         if use_agent_mode:
#             print(f"🤖 Using Agent RAG (multi-step reasoning)...")
#             answer, chunks, agent_metadata = answer_with_agent(question, history)
            
#             # Merge metadata
#             final_metadata = {**routing_metadata, **agent_metadata}
            
#             return answer, chunks, final_metadata
#         else:
#             print(f"⚡ Using Simple RAG (fast path)...")
#             answer, chunks, simple_metadata = answer_question(question, history)
            
#             # Merge metadata
#             final_metadata = {**routing_metadata, **simple_metadata}
            
#             return answer, chunks, final_metadata
            
#     except Exception as e:
#         print(f"Error in hybrid answer: {e}")
#         import traceback
#         traceback.print_exc()
        
#         return f"Error: {str(e)}", [], {"error": str(e)}

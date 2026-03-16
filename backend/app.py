import gradio as gr
from dotenv import load_dotenv
from implementations.answers import answer_question, answer_question_hybrid

load_dotenv(override=True)
gr.close_all()

def format_context(context, routing_metadata=None):
    """Format retrieved context for display in the UI.

    Supports both dict-based chunks (the pipeline/database format)
    and objects with attributes (older formats).
    """
    def _get_field(obj, name, default=None):
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    result = ""
    
    # Add routing metadata if available
    if routing_metadata:
        # Check if agent mode
        is_agent = routing_metadata.get('agent_mode', False)
        routing_decision = routing_metadata.get('routing_decision', 'unknown')
        
        # Color scheme based on mode
        if is_agent or routing_decision == 'agent':
            bg_color = '#f0fff4'
            border_color = '#38a169'
            title_color = '#38a169'
            icon = '🤖 Agent RAG'
        else:
            bg_color = '#f0f8ff'
            border_color = '#1e90ff'
            title_color = '#1e90ff'
            icon = '⚡ Simple RAG'
        
        result += f"<div style='background-color: {bg_color}; border-left: 4px solid {border_color}; padding: 12px; margin-bottom: 15px; border-radius: 4px;'>\n"
        result += f"<h3 style='color: {title_color}; margin-top: 0;'>{icon}</h3>\n"
        
        # Show routing decision
        if routing_decision != 'unknown':
            result += f"<p style='margin: 4px 0;'><b>Mode:</b> {routing_decision.upper()}</p>\n"
        
        # Show complexity info
        if 'complexity_level' in routing_metadata:
            result += f"<p style='margin: 4px 0;'><b>Complexity:</b> {routing_metadata.get('complexity_level', 'unknown')}</p>\n"
        
        if 'complexity_score' in routing_metadata and routing_metadata.get('complexity_score') != 'N/A':
            result += f"<p style='margin: 4px 0;'><b>Score:</b> {routing_metadata.get('complexity_score'):.2f}</p>\n"
        
        # Show agent-specific info
        if is_agent or routing_decision == 'agent':
            if 'analysis_type' in routing_metadata:
                result += f"<p style='margin: 4px 0;'><b>Analysis Type:</b> {routing_metadata.get('analysis_type')}</p>\n"
            if 'agent_steps' in routing_metadata:
                steps = ' → '.join(routing_metadata.get('agent_steps', []))
                result += f"<p style='margin: 4px 0;'><b>Agent Steps:</b> {steps}</p>\n"
            if 'insights_count' in routing_metadata:
                result += f"<p style='margin: 4px 0;'><b>Insights Generated:</b> {routing_metadata.get('insights_count')}</p>\n"
        
        # Show reasoning
        if routing_metadata.get('reasoning'):
            result += f"<p style='margin: 4px 0;'><b>Reasoning:</b> {routing_metadata.get('reasoning', '')}</p>\n"
        
        result += "</div>\n"
    
    result += "<h2 style='color: #ff7800;'>Relevant Context</h2>\n\n"
    for i, doc in enumerate(context or [], 1):
        meta = _get_field(doc, "metadata", {}) or {}
        # metadata might be an object or dict
        if isinstance(meta, dict):
            source = meta.get("source", "Unknown")
            page = meta.get("page_index", "Unknown")
        else:
            source = getattr(meta, "source", "Unknown")
            page = getattr(meta, "page_index", "Unknown")

        content = _get_field(doc, "page_content", _get_field(doc, "text", "")) or ""

        result += f"<span style='color: #ff7800;'>Chunk: {i}. In Page: {page}</span>\n"
        result += f"<span style='color: #ff7800;'>Source: {source}</span>\n\n"
        result += str(content) + "\n\n"

    return result


def chat(history):
    """Process chat message and return response with context."""
    try:
        # history from Gradio is list of [user_message, assistant_response] pairs or single messages
        if not history or len(history) == 0:
            return history, format_context([])
        
        # Get the last message (user's question)
        # Gradio Chatbot format: list of tuples or dicts
        last_item = history[-1]
        
        # Handle tuple format (user_message, assistant_message)
        if isinstance(last_item, (tuple, list)):
            last_message = last_item[0] if len(last_item) > 0 else ""
        # Handle dict format with "content" key
        elif isinstance(last_item, dict) and "content" in last_item:
            last_message = last_item["content"]
        else:
            last_message = str(last_item)
        
        # Ensure it's a string
        last_message = str(last_message).strip()
        
        if not last_message:
            return history, format_context([])
        
        # Get prior history (for context in rewriting)
        # Convert to format expected by answer_question
        prior = []
        for i, item in enumerate(history[:-1]):
            if isinstance(item, (tuple, list)):
                if len(item) >= 1:
                    prior.append({"role": "user", "content": str(item[0])})
                if len(item) >= 2:
                    prior.append({"role": "assistant", "content": str(item[1])})
            elif isinstance(item, dict):
                if "content" in item:
                    prior.append({"role": item.get("role", "user"), "content": str(item["content"])})
        
        # Get answer with hybrid routing (uses agent tools for complex questions)
        answer, context, routing_metadata = answer_question_hybrid(last_message, prior)
        
        # Update history with assistant response
        if isinstance(last_item, (tuple, list)):
            history[-1] = (last_item[0], answer) if isinstance(last_item, tuple) else [last_item[0], answer]
        elif isinstance(last_item, dict):
            history.append({"role": "assistant", "content": answer})
        
        # Format context with routing metadata
        return history, format_context(context, routing_metadata)
    except Exception as e:
        print(f"Error in chat: {e}")
        import traceback
        traceback.print_exc()
        return history, f"<p style='color:red;'>Error: {str(e)}</p>"


def main():
    def put_message_in_chatbot(message, history):
        return "", history + [{"role": "user", "content": message}]

    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

    with gr.Blocks(title="Financial Expert Assistant") as ui:
        gr.Markdown("# 🏢 Financial Expert Assistant\nAsk me anything about financial reports!")

        with gr.Row():
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(label="💬 Conversation", height=600)
                message = gr.Textbox(
                    label="Your Question",
                    placeholder="Ask anything about Your Financial Report...",
                    show_label=False,
                )

            with gr.Column(scale=1):
                context_markdown = gr.Markdown(
                    label="📚 Retrieved Context",
                    value="*Retrieved context will appear here*",
                    container=True,
                    height=600,
                )

        message.submit(put_message_in_chatbot, inputs=[message, chatbot], outputs=[message, chatbot]
                    ).then(chat, inputs=chatbot, outputs=[chatbot, context_markdown])

    ui.launch(inbrowser=True, theme=theme)


if __name__ == "__main__":
    main()
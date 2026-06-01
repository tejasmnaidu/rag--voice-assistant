
# voice_assistant/response_generation.py

import logging
from typing import Tuple, List, Dict

from openai import OpenAI
from groq import Groq
import ollama

from voice_assistant.config import Config
from voice_assistant.citation_manager import get_citation_manager

logger = logging.getLogger(__name__)


def generate_response(model: str, api_key: str, chat_history: list, 
                     local_model_path: str = None, 
                     retrieved_docs: List[Dict] = None,
                     include_citations: bool = True) -> Tuple[str, Dict]:
    """
    Generate a response using the specified model with source citations.
    
    Args:
        model (str): The model to use for response generation ('openai', 'groq', 'local').
        api_key (str): The API key for the response generation service.
        chat_history (list): The chat history as a list of messages.
        local_model_path (str): The path to the local model (if applicable).
        retrieved_docs (List[Dict]): Retrieved documents from RAG system.
        include_citations (bool): Whether to include source citations in response context.

    Returns:
        Tuple[str, Dict]: (response_text, citation_info)
    """
    try:
        # Initialize citation tracking
        citation_manager = get_citation_manager()
        citation_manager.reset()
        
        # Add retrieved documents to citation manager
        if retrieved_docs and include_citations:
            citation_manager.add_retrieved_sources(retrieved_docs)
            # Augment chat history with source context
            augmented_history = _augment_chat_history_with_sources(chat_history, retrieved_docs)
        else:
            augmented_history = chat_history
        
        # Generate response
        response_text = ""
        if model == 'openai':
            response_text = _generate_openai_response(api_key, augmented_history)
        elif model == 'groq':
            response_text = _generate_groq_response(api_key, augmented_history)
        elif model == 'ollama':
            response_text = _generate_ollama_response(augmented_history)
        elif model == 'local':
            response_text = "Generated response from local model"
        else:
            raise ValueError("Unsupported response generation model")
        
        # Track citations used in response
        if retrieved_docs and include_citations:
            citation_manager.track_citation_usage(response_text=response_text)
        
        # Get citations summary
        citations_info = citation_manager.get_summary()
        
        return response_text, citations_info
        
    except Exception as e:
        logger.error(f"Failed to generate response: {e}")
        return "Error in generating response", {"total_sources": 0, "top_citations": [], "error": str(e)}


def _augment_chat_history_with_sources(chat_history: list, 
                                       retrieved_docs: List[Dict]) -> list:
    """
    Augment chat history with retrieved document context.
    
    Args:
        chat_history: Original chat history
        retrieved_docs: Retrieved documents from RAG system
    
    Returns:
        Augmented chat history with source context
    """
    if not retrieved_docs:
        return chat_history
    
    # Create a system message with source context
    sources_context = _format_sources_for_context(retrieved_docs)
    
    augmented_history = chat_history.copy()
    
    # Insert source context before user message if not already present
    system_message_exists = any(msg.get("role") == "system" for msg in augmented_history)
    
    if not system_message_exists and sources_context:
        augmented_history.insert(0, {
            "role": "system",
            "content": sources_context
        })
    elif system_message_exists and sources_context:
        # Append to existing system message
        for msg in augmented_history:
            if msg.get("role") == "system":
                msg["content"] += f"\n\n{sources_context}"
                break
    
    return augmented_history


def _format_sources_for_context(retrieved_docs: List[Dict], max_docs: int = 5) -> str:
    """
    Format retrieved documents for inclusion in the system prompt.
    
    Args:
        retrieved_docs: Retrieved documents
        max_docs: Maximum number of documents to include
    
    Returns:
        Formatted source context string
    """
    if not retrieved_docs:
        return ""
    
    sources_text = "You have access to the following sources to answer the question:\n\n"
    
    for idx, doc in enumerate(retrieved_docs[:max_docs], 1):
        metadata = doc.get("metadata", {})
        chunk_text = doc.get("chunk", "")[:300]  # Limit chunk size
        source_name = metadata.get("source", f"Source {idx}")
        page = metadata.get("page", "")
        
        source_info = f"[{idx}] {source_name}"
        if page:
            source_info += f" (Page {page})"
        source_info += f":\n{chunk_text}\n"
        
        sources_text += source_info + "\n"
    
    sources_text += "\nUse these sources to provide accurate, grounded answers. Include citations like [1], [2], etc. when referencing sources."
    
    return sources_text


def _generate_openai_response(api_key: str, chat_history: list) -> str:
    """Generate response using OpenAI API."""
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=Config.OPENAI_LLM,
        messages=chat_history
    )
    return response.choices[0].message.content


def _generate_groq_response(api_key: str, chat_history: list) -> str:
    """Generate response using Groq API."""
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=Config.GROQ_LLM,
        messages=chat_history
    )
    return response.choices[0].message.content


def _generate_ollama_response(chat_history: list) -> str:
    """Generate response using Ollama."""
    response = ollama.chat(
        model=Config.OLLAMA_LLM,
        messages=chat_history,
    )
    return response['message']['content']

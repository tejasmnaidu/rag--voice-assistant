from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import PyPDF2
from typing import List, Dict
import io
import os
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

from voice_assistant.rag.vector_store import VectorStore
from voice_assistant.rag.retriever import init_retriever, retrieve
from voice_assistant.response_generation import generate_response
from voice_assistant.api_key_manager import get_response_api_key
from voice_assistant.config import Config

app = FastAPI(title="Spark Voice Assistant RAG API")

vector_store = None

class QueryModel(BaseModel):
    query: str
    chat_history: list = None

@app.on_event("startup")
def startup_event():
    global vector_store
    
    if os.path.exists("vector_store.faiss") and os.path.exists("vector_store_chunks.pkl"):
        logging.info("Persistent DB found! Booting FAISS Index from disk into RAM...")
        vector_store = VectorStore()
        vector_store.load_index("vector_store")
        init_retriever(vector_store)
        logging.info("System successfully initialized from Persistent DB state.")

@app.get("/health")
def health_check():
    return {"status": "OK"}

@app.post("/upload")
async def upload_pdf(files: List[UploadFile] = File(...)):
    global vector_store
    
    try:
        chunks_data = []
        chunk_idx = 1
        
        def smart_chunk(raw_text, max_chars=500, overlap=100):
            import re
            sentences = re.split(r'(?<=[.!?])\s+', raw_text)
            result_chunks = []
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= max_chars:
                    current_chunk += sentence + " "
                else:
                    if current_chunk:
                        result_chunks.append(current_chunk.strip())
                    if result_chunks:
                        prev = result_chunks[-1]
                        overlap_str = prev[-overlap:] if len(prev) >= overlap else prev
                        boundary = max(overlap_str.find('. '), overlap_str.find('! '), overlap_str.find('? '))
                        if boundary != -1:
                            overlap_str = overlap_str[boundary + 2:]
                        current_chunk = overlap_str.strip() + " " + sentence + " "
                    else:
                        current_chunk = sentence + " "
            if current_chunk.strip():
                result_chunks.append(current_chunk.strip())
            return result_chunks
            
        for file in files:
            if not file.filename.endswith(".pdf"):
                continue
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(await file.read()))
            doc_name = file.filename
            
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    page_chunks = smart_chunk(page_text)
                    for c in page_chunks:
                        chunks_data.append({
                            "text": c,
                            "metadata": {
                                "chunk_id": chunk_idx,
                                "source": doc_name,
                                "page": page_num
                            }
                        })
                        chunk_idx += 1

        if not chunks_data:
            raise HTTPException(status_code=400, detail="No valid PDF content found.")

        vector_store = VectorStore()
        vector_store.add_documents(chunks_data)
        vector_store.save_index("vector_store")  # PERSIST TO DISK
        init_retriever(vector_store)

        logging.info(f"PDFs processed successfully. Total chunks generated and stored: {len(chunks_data)}")
        return {"message": "Successfully processed PDFs", "chunks": len(chunks_data), "documents_processed": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
def query_rag(req: QueryModel):
    global vector_store
    
    try:
        user_input = req.query
        response_api_key = get_response_api_key()
        
        # 0. Personal Assistant Memory Intercept (To-Do list & Facts)
        memory_file_path = "memory.txt"
        user_input_lower = user_input.lower()
        
        # Simple rule-based learning: intercept commands asking to remember
        is_memory_command = False
        memory_triggers = ["remember ", "remember that ", "add to todo", "add to my to-do", "add to my to do", "note this", "todo:"]
        for trigger in memory_triggers:
            if trigger in user_input_lower:
                is_memory_command = True
                with open(memory_file_path, "a", encoding="utf-8") as f:
                    # Strip the command prefix heuristically or just save the whole thing
                    f.write(f"- {user_input.strip()}\n")
                break
        
        total_start = time.time()
        
        relevant_results = []
        if vector_store is not None and vector_store.index is not None and vector_store.index.ntotal > 0:
            # LLM-Based Query Rewriting for higher retrieval semantic density
            rewrite_start = time.time()
            rewrite_prompt = f"Rewrite this query into a highly descriptive search query optimized for semantic document retrieval: {user_input}"
            rewritten_query = generate_response(
                Config.RESPONSE_MODEL, 
                response_api_key, 
                [{"role": "user", "content": rewrite_prompt}], 
                Config.LOCAL_MODEL_PATH
            ).strip()
            rewrite_time = time.time() - rewrite_start
            
            logging.info(f"Query Rewrite: '{user_input}' -> '{rewritten_query}' (Time: {rewrite_time:.2f}s)")
            
            retrieval_start = time.time()
            relevant_results = retrieve(rewritten_query)
            retrieval_time = time.time() - retrieval_start
            
            logging.info(f"Retriever: Extracted {len(relevant_results)} relevant chunks from Vector DB (Time: {retrieval_time:.2f}s)")
        
        context = ""
        sources = []
        if relevant_results:
            context = "\n\n".join([res["chunk"] for res in relevant_results])
            for res in relevant_results:
                meta = res.get("metadata", {})
                sources.append({
                    "chunk": res["chunk"],
                    "document_name": meta.get("source", "Unknown Document"),
                    "page_number": meta.get("page", "?"),
                    "chunk_id": meta.get("chunk_id", res['index'])
                })
        
        if context:
            query_for_llm = f"Use the following context to answer the question:\n{context}\n\nQuestion: {user_input}"
        else:
            query_for_llm = user_input
        
        # Retrieve any saved persistent memory dynamically
        assistant_memory = ""
        if os.path.exists("memory.txt"):
            with open("memory.txt", "r", encoding="utf-8") as f:
                memory_db = f.read().strip()
            if memory_db:
                assistant_memory = f"\n\nHere are the user's saved notes, to-dos, and permanent memory across sessions. Always keep these in mind if applicable:\n{memory_db}"
        
        # Hydrate chat history appropriately
        if req.chat_history:
            chat_history = req.chat_history
            # Ensure system prompt has memory dynamically bound to it via iteration
            if chat_history and chat_history[0].get("role") == "system":
                chat_history[0]["content"] = f"You are a helpful personal assistant.{assistant_memory}"
        else:
            chat_history = [{"role": "system", "content": f"You are a helpful personal assistant.{assistant_memory}"}]
            
        # Safely insert the newly augmented prompt without modifying the original user log sent from UI
        modified_history = chat_history.copy()
        if modified_history and modified_history[-1]["role"] == "user":
            modified_history[-1] = {"role": "user", "content": query_for_llm}
        else:
            modified_history.append({"role": "user", "content": query_for_llm})
            
        gen_start = time.time()
        response_text = generate_response(Config.RESPONSE_MODEL, response_api_key, modified_history, Config.LOCAL_MODEL_PATH)
        gen_time = time.time() - gen_start
        
        total_time = time.time() - total_start
        logging.info(f"RAG Cycle Complete -> Total Latency: {total_time:.2f}s | Gen Time: {gen_time:.2f}s | Retrieved Chunks: {len(relevant_results)}")
        
        return {
            "answer": response_text,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

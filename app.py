# app.py

import streamlit as st
import time
import streamlit.components.v1 as components
import os
import logging
import threading
import tempfile
from datetime import datetime
import base64
import json
import PyPDF2

from voice_assistant.rag.vector_store import VectorStore
from voice_assistant.audio import record_audio, play_audio, stop_audio
from voice_assistant.transcription import transcribe_audio
from voice_assistant.response_generation import generate_response
from voice_assistant.text_to_speech import text_to_speech
from voice_assistant.utils import delete_file
from voice_assistant.config import Config
from voice_assistant.api_key_manager import get_transcription_api_key, get_response_api_key, get_tts_api_key

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to autoplay audio
def autoplay_audio(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)

# Function for recording state
def start_recording():
    st.session_state.status = "Listening..."
    with st.spinner("Recording..."):
        record_audio(Config.INPUT_AUDIO)
    st.session_state.status = "Processing..."
    return True


# Main app function
def main():
    st.set_page_config(
        page_title="Spark Voice Assistant",
        page_icon="🎤",
        layout="wide",
    )
    st.markdown("""
        <style>
        html, body, .stApp {
            color: #d1d5db;
        }

        .block-container {
            background-color: #0d0d0d;
            padding: 2rem;
            border-radius: 12px;
        }

        /* Title */
        .stMarkdown h1 {
            font-size: 2rem;
            font-weight: 600;
            color: #f3f4f6;
            text-align: center;
        }

        /* Chat bubbles */
        .stChatMessage {
            background-color: #1f2937;
            border: 1px solid #374151;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        /* Primary buttons */
        .stButton button {
            border-radius: 8px;
            padding: 0.5rem 1.2rem;
            background-color: #1f2937;  /* dark gray */
            color: #f3f4f6;
            font-weight: 500;
            border: 1px solid #374151;
        }
        .stButton button:hover {
            background-color: #374151;  /* slightly lighter gray */
            color: #f9fafb;
        }

        /* Stop button styling */
        div[data-testid="stButton"][aria-label="stop_button_top"] button {
            background-color: #ef4444 !important;
            color: white !important;
            border: none !important;
        }
        div[data-testid="stButton"][aria-label="stop_button_top"] button:hover {
            background-color: #dc2626 !important;
        }

        /* Inputs & dropdowns */
        .stTextInput > div > div > input,
        .stSelectbox > div > div {
            background-color: #1f2937 !important;
            color: #d1d5db !important;
            border: 1px solid #374151 !important;
        }

        section[tabindex] {
            background-color: #111827 !important;
            border: 1px solid #374151 !important;
            border-radius: 8px;
        }
        /* Mobile responsiveness */
        @media (max-width: 600px) {
            .block-container { padding: 1rem; }
            .stChatMessage { font-size: 0.95rem; }
        }
        </style>
    """, unsafe_allow_html=True)






    
    st.sidebar.title("Settings")
    # Theme toggle
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'
    theme_choice = st.sidebar.radio("Theme", ['dark', 'light'], index=0 if st.session_state.theme=='dark' else 1)
    st.session_state.theme = theme_choice
    
    
    tts_options = ["openai", "elevenlabs", "deepgram", "melotts", "cartesia", "local"]
    selected_tts = st.sidebar.selectbox(
        "Text-to-Speech Model",
        tts_options,
        index=tts_options.index(Config.TTS_MODEL) if Config.TTS_MODEL in tts_options else 0
    )
    
    
    if selected_tts == "openai":
        tts_voice = st.sidebar.selectbox(
            "OpenAI Voice",
            ["nova", "alloy", "echo", "fable", "onyx", "shimmer"],
            index=0
        )
    elif selected_tts == "elevenlabs":
        tts_voice = st.sidebar.selectbox(
            "ElevenLabs Voice",
            ["Paul J.", "Rachel", "Domi", "Adam", "Antoni", "Bella"],
            index=0
        )
    
    
    transcription_options = ["groq", "openai", "deepgram", "fastwhisperapi", "local"]
    selected_transcription = st.sidebar.selectbox(
        "Transcription Model",
        transcription_options,
        index=transcription_options.index(Config.TRANSCRIPTION_MODEL) if Config.TRANSCRIPTION_MODEL in transcription_options else 0
    )
    
    
    response_options = ["groq", "openai", "ollama", "local"]
    selected_response = st.sidebar.selectbox(
        "Response Model",
        response_options,
        index=response_options.index(Config.RESPONSE_MODEL) if Config.RESPONSE_MODEL in response_options else 0
    )
    
    
    if selected_response == "groq":
        llm_options = ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"]
        selected_llm = st.sidebar.selectbox(
            "Groq LLM",
            llm_options,
            index=llm_options.index(Config.GROQ_LLM) if Config.GROQ_LLM in llm_options else 0
        )
    elif selected_response == "openai":
        llm_options = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
        selected_llm = st.sidebar.selectbox(
            "OpenAI LLM",
            llm_options,
            index=llm_options.index(Config.OPENAI_LLM) if Config.OPENAI_LLM in llm_options else 0
        )
    elif selected_response == "ollama":
        llm_options = ["llama3:8b", "llama3:70b", "mistral:7b"]
        selected_llm = st.sidebar.selectbox(
            "Ollama LLM",
            llm_options,
            index=llm_options.index(Config.OLLAMA_LLM) if Config.OLLAMA_LLM in llm_options else 0
        )
    
    
    if st.sidebar.button("Apply Settings"):
        Config.TTS_MODEL = selected_tts
        Config.TRANSCRIPTION_MODEL = selected_transcription
        Config.RESPONSE_MODEL = selected_response
        
        if selected_response == "groq":
            Config.GROQ_LLM = selected_llm
        elif selected_response == "openai":
            Config.OPENAI_LLM = selected_llm
        elif selected_response == "ollama":
            Config.OLLAMA_LLM = selected_llm
            
        st.sidebar.success("Settings applied!")
    

    # Document Upload for RAG
    with st.sidebar.expander("Document Upload (RAG)", expanded=False):
        uploaded_files = st.file_uploader("Upload PDF documents", type=["pdf"], accept_multiple_files=True)
        if uploaded_files:
            if st.button("Process PDFs"):
                with st.spinner("Processing PDFs..."):
                    try:
                        import requests
                        files_payload = [("files", (f.name, f.getvalue(), "application/pdf")) for f in uploaded_files]
                        res = requests.post("http://localhost:8080/upload", files=files_payload)
                        if res.status_code == 200:
                            data = res.json()
                            st.success(f"Successfully processed {data['documents_processed']} PDFs into {data['chunks']} chunks globally via FastAPI Database!")
                        else:
                            st.error(f"Error from FastAPI backend: {res.text}")
                    except Exception as e:
                        st.error(f"Error processing PDFs: {str(e)}")

    # Service Status
    with st.sidebar.expander("Service Status", expanded=False):
        if st.button("Check FastWhisperAPI"):
            try:
                from voice_assistant.transcription import check_fastwhisperapi
                check_fastwhisperapi()
                st.success("FastWhisperAPI is running")
            except Exception as e:
                st.error(f"FastWhisperAPI is not running: {str(e)}")
        
        if st.button("Check MeloTTS"):
            try:
                import requests
                response = requests.get(f"http://localhost:{Config.TTS_PORT_LOCAL}/health")
                if response.status_code == 200:
                    st.success("MeloTTS is running")
                else:
                    st.error("MeloTTS is not responding properly")
            except Exception as e:
                st.error(f"MeloTTS is not running: {str(e)}")

    
    st.markdown("""
        <h1 style="text-align:center; margin-bottom: 0.5rem;">🤖 Spark Voice Assistant</h1>
        <p style="text-align:center; font-size: 1rem; color: #9ca3af;">
            Your personal assistant — ready to help.
        </p>
    """, unsafe_allow_html=True)


    
    # Metrics display row
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        st.metric(label="Transcription", value=Config.TRANSCRIPTION_MODEL)
    with col2:
        st.metric(label="Response", value=Config.RESPONSE_MODEL)
    with col3:
        st.metric(label="TTS", value=Config.TTS_MODEL)
    with col4:
        status = st.session_state.get('status', 'Idle')
        st.metric(label="Status", value=status)

    
    # Stop speaking button
    stop_col = st.columns([1])[0]
    with stop_col:
        if st.button("🛑 Stop Speaking", key="stop_button_top", use_container_width=True):
            stop_audio()
            st.info("Playback stopped. You can now speak again.")

    
    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = [{
            "role": "system",
            "content": """You are spark, a comprehensive personal assistant with access to the user's calendar, emails, tasks, weather information, news, contacts, and expenses. 
            Use the provided functions to retrieve information and assist the user. Always provide thoughtful and detailed responses. Assume today's date is 2025-03-10"""
        }]
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hello! I'm Spark"
        })
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("🎤 Record", key="record_button", use_container_width=True):
            recording_complete = start_recording()
            if recording_complete:
                try:
                    transcription_api_key = get_transcription_api_key()
                    t1 = time.time()
                    with st.spinner("Transcribing audio..."):
                        user_input = transcribe_audio(Config.TRANSCRIPTION_MODEL, transcription_api_key, Config.INPUT_AUDIO, Config.LOCAL_MODEL_PATH)
                    if not user_input:
                        st.error("No speech detected. Please try again.")
                    else:
                        process_user_input(user_input, chat_container)
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    logging.error(f"An error occurred: {e}")

        # Browser-side waveform demo (visual only)
        components.html('''
        <div style="display:flex;flex-direction:column;align-items:center;">
                <canvas id="wave" width="300" height="60" style="width:100%;max-width:300px;border-radius:6px;background:#0b1220;display:block;"></canvas>
          <div style="font-size:12px;color:#9ca3af;margin-top:6px;">Browser mic waveform (visual only)</div>
        </div>
        <script>
        const canvas = document.getElementById('wave');
                const ctx = canvas.getContext('2d');
                const DPR = window.devicePixelRatio || 1;
                function resizeCanvas(){
                    // set canvas internal size for crisp rendering
                    const w = canvas.clientWidth;
                    const h = 60;
                    canvas.width = Math.max(1, Math.floor(w * DPR));
                    canvas.height = Math.max(1, Math.floor(h * DPR));
                    canvas.style.height = h + 'px';
                    ctx.setTransform(1,0,0,1,0,0);
                    ctx.scale(DPR, DPR);
                }
                resizeCanvas();
                window.addEventListener('resize', resizeCanvas);

                navigator.mediaDevices.getUserMedia({audio:true}).then(stream=>{
                    const audioCtx = new (window.AudioContext||window.webkitAudioContext)();
                    const source = audioCtx.createMediaStreamSource(stream);
                    const analyser = audioCtx.createAnalyser();
                    analyser.fftSize = 256;
                    source.connect(analyser);
                    const data = new Uint8Array(analyser.frequencyBinCount);
                    function draw(){
                        requestAnimationFrame(draw);
                        analyser.getByteTimeDomainData(data);
                        const W = canvas.width / DPR;
                        const H = canvas.height / DPR;
                        ctx.fillStyle = '#0b1220'; ctx.fillRect(0,0,W,H);
                        ctx.lineWidth = 2; ctx.strokeStyle = '#34d399'; ctx.beginPath();
                        const sliceWidth = W / data.length;
                        let x = 0;
                        for(let i=0;i<data.length;i++){
                            const v = data[i]/128.0;
                            const y = v*H/2;
                            if(i===0) ctx.moveTo(x,y);
                            else ctx.lineTo(x,y);
                            x+=sliceWidth;
                        }
                        ctx.stroke();
                    }
                    draw();
                }).catch(e=>{console.log('mic denied',e)});
        </script>
        ''', height=140)
    
    
    # Voice selection in main UI (mirrors sidebar)
    voice_cols = st.columns([1,3])
    with voice_cols[0]:
        tts_voice_main = st.selectbox("Voice", ["default", "nova", "alloy", "echo", "fable", "onyx", "shimmer"], index=0)

    user_input = st.chat_input("Or type your message here...")
    if user_input:
        process_user_input(user_input, chat_container)

def process_user_input(user_input, chat_container):
    
    st.session_state.status = 'Thinking...'
    st.session_state.messages.append({"role": "user", "content": user_input})
    with chat_container:
        with st.chat_message("user"):
            st.write(user_input)
    
    
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    
    if "goodbye" in user_input.lower() or "arrivederci" in user_input.lower():
        with chat_container:
            with st.chat_message("assistant"):
                st.write("Goodbye! It was nice chatting with you.")
        st.session_state.chat_history.append({"role": "assistant", "content": "Goodbye! It was nice chatting with you."})
        return
    
    # Generate response with a spinner to show loading and collect latency metrics
    with st.spinner("Thinking..."):
        try:
            import requests
            total_start = time.time()
            
            payload = {
                "query": user_input,
                "chat_history": st.session_state.chat_history
            }
            
            try:
                res = requests.post("http://localhost:8080/query", json=payload)
                
                if res.status_code == 200:
                    data = res.json()
                    response_text = data["answer"]
                    sources = data.get("sources", [])
                    
                    citations = ""
                    if sources:
                        citations = "\n\n**Sources:**\n"
                        for s in sources:
                            citations += f"- Document: {s['document_name']} (Page {s['page_number']}), Chunk {s['chunk_id']}\n"
                            
                    total_time = time.time() - total_start
                    response_text += citations
                else:
                    response_text = f"Error from backend API: {res.text}"
                    logging.error(f"Backend Request Failed: {res.text}")
                    
            except Exception as e:
                response_text = f"Connection Error: {e}. Ensure FastAPI backend is running on port 8080."
                logging.error(f"Connection Error: {e}")
            
            # Stream / typing animation for assistant reply
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            with chat_container:
                with st.chat_message("assistant"):
                    placeholder = st.empty()
                    # reveal response word-by-word for typing effect
                    words = response_text.split()
                    displayed = ""
                    for w in words:
                        displayed += (" " if displayed else "") + w
                        placeholder.markdown(displayed)
                        time.sleep(0.03)
                    # ensure final text
                    placeholder.markdown(response_text)
            
            
            st.session_state.chat_history.append({"role": "assistant", "content": response_text})
            st.session_state.status = 'Idle'
            
            
            if Config.TTS_MODEL in ['openai', 'elevenlabs', 'melotts', 'cartesia']:
                output_file = 'output.mp3'
            else:
                output_file = 'output.wav'
            
            
            tts_api_key = get_tts_api_key()
            
            
            with st.spinner("Generating audio response..."):
                text_to_speech(Config.TTS_MODEL, tts_api_key, response_text, output_file, Config.LOCAL_MODEL_PATH)
                
                
                if Config.TTS_MODEL != "cartesia":
                    autoplay_audio(output_file)
                    
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            logging.error(f"An error occurred: {e}")
            
    # Optionally clean up files (commented out to match your original behavior)
    # delete_file(Config.INPUT_AUDIO)
    # if Config.TTS_MODEL != "cartesia":
    #     delete_file(output_file)

if __name__ == "__main__":
    main()
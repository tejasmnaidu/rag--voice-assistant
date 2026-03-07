# SPARK – AI Voice Assistant

SPARK is an AI-powered voice assistant designed to interact with users through natural speech.
It integrates speech recognition, large language models, and text-to-speech generation to enable conversational interaction between humans and AI systems.

The project supports multiple modern AI APIs and also allows integration with local models, making it a flexible platform for experimenting with voice-based AI systems.

---

# Features

## Speech-to-Text Transcription

The assistant converts spoken audio into text using advanced transcription models.

Supported providers include:

* OpenAI Whisper
* Groq Whisper
* Deepgram
* FastWhisper API
* Local models

---

## Intelligent Response Generation

SPARK generates contextual responses using large language models.

Supported providers include:

* OpenAI
* Groq
* Ollama (local LLMs)

---

## Text-to-Speech Generation

The assistant converts generated responses back into speech.

Supported providers include:

* Deepgram
* ElevenLabs
* OpenAI
* Cartesia AI
* MeloTTS
* Local models

---

## Modular Architecture

The system follows a modular architecture, allowing developers to easily switch between different AI models for transcription, response generation, and speech synthesis.

Example module structure:

```id="n52n0y"
voice_assistant/
├── audio.py
├── transcription.py
├── response_generation.py
├── text_to_speech.py
├── api_key_manager.py
├── config.py
└── utils.py
```

---

# System Architecture

```id="xv4jwe"
User Speech
     ↓
Audio Recording
     ↓
Speech-to-Text (Transcription)
     ↓
Language Model Response Generation
     ↓
Text-to-Speech Conversion
     ↓
Audio Response to User
```

---

# Project Structure

```id="aj0rrq"
SPARK-Voice-Assistant
│
├── app.py
├── run_voice_assistant.py
├── setup.py
├── requirements.txt
├── README.md
│
├── voice_assistant/
│   ├── audio.py
│   ├── transcription.py
│   ├── response_generation.py
│   ├── text_to_speech.py
│   ├── config.py
│   └── utils.py
│
└── voice_samples/
```

---

# Installation

## Clone the Repository

```id="pq5qmx"
git clone https://github.com/tejas-m-naidu/spark-voice-assistant.git
cd spark-voice-assistant
```

---

## Create a Virtual Environment

```id="dwcxcb"
python -m venv venv
```

Activate the environment:

Windows:

```id="or6bpt"
venv\Scripts\activate
```

Linux / Mac:

```id="sz40dh"
source venv/bin/activate
```

---

## Install Dependencies

```id="az2vrs"
pip install -r requirements.txt
```

---

# Environment Configuration

Create a `.env` file in the root directory and add your API keys.

Example:

```id="4s85r2"
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
LOCAL_MODEL_PATH=path/to/local/model
```

---

# Model Configuration

Edit `voice_assistant/config.py` to select which models should be used.

Example:

```python id="exg28d"
class Config:

    TRANSCRIPTION_MODEL = 'groq'
    RESPONSE_MODEL = 'groq'
    TTS_MODEL = 'deepgram'
```

Different providers can be selected depending on available APIs.

---

# Running the Voice Assistant

Run the assistant using:

```id="8vdpyg"
python run_voice_assistant.py
```

The assistant will start listening through the microphone and respond using synthesized speech.

---

# Running the Web Interface

The project also provides a Streamlit-based interface.

```id="4pbm4g"
streamlit run app.py
```

This launches a browser-based interface for interacting with the assistant.

---

# Technologies Used

* Python
* SpeechRecognition
* OpenAI API
* Groq API
* Deepgram
* ElevenLabs
* Streamlit
* FastAPI
* Ollama (local language models)

---

# Academic Context

This project was developed as part of a college mini project to explore the design and implementation of AI-powered voice assistants using modern speech and language models.

---

# Author

Tejas M Naidu
AI / ML Enthusiast

GitHub:
https://github.com/tejas-m-naidu

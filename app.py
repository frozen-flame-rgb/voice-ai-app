import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
from streamlit_mic_recorder import mic_recorder
from PIL import Image
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JARVIS", page_icon="🤖", layout="centered")

# Custom JARVIS Styling
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stApp {background-color: #000000; color: #00ffcc;}
        .stButton>button {width: 100%; border-radius: 20px; background-color: #003333; color: #00ffcc; border: 1px solid #00ffcc;}
        .stCheckbox>label {color: #00ffcc; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# API Setup
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Key Missing in Streamlit Secrets")
    st.stop()

# --- 2. LOGIC FUNCTIONS ---
def clean_text(text):
    """Removes Markdown symbols so the voice synth sounds natural."""
    clean = re.sub(r'[*#`]', '', text) 
    return clean.strip()

async def speak(text):
    """Converts text to speech using Edge TTS."""
    OUTPUT_FILE = "jarvis_reply.mp3"
    spoken_text = clean_text(text)
    communicate = edge_tts.Communicate(spoken_text, "en-GB-RyanNeural")
    await communicate.save(OUTPUT_FILE)
    return OUTPUT_FILE

# --- 3. THE INTERFACE ---
st.markdown("<h1 style='text-align: center; color: #00ffcc; font-family: Courier New;'>J.A.R.V.I.S.</h1>", unsafe_allow_html=True)

# Vision System
use_vision = st.checkbox("👁️ Enable Vision System")
camera_image = st.camera_input("Visual Feed") if use_vision else None

# Voice System
st.write("---")
c1, c2, c3 = st.columns([1, 3, 1])
with c2:
    audio_input = mic_recorder(
        start_prompt="🔴 VOICE COMMAND",
        stop_prompt="⏹️ PROCESSING...",
        key="recorder",
        just_once=True,
        use_container_width=True
    )

# Typing Search Bar (at the bottom)
typed_input = st.chat_input("Search or command JARVIS...")

# --- 4. EXECUTION LOGIC ---
user_prompt = None
audio_bytes = None

# Input selection: Priority to text if typed, otherwise voice
if typed_input:
    user_prompt = typed_input
elif audio_input:
    audio_bytes = audio_input['bytes']
    user_prompt = "Voice Input"

if user_prompt:
    status = st.empty()
    status.info("⚡ Authenticating...")

    try:
        # Using the specific model you confirmed works
        model = genai.GenerativeModel("models/gemini-flash-latest")
        
        inputs = []
        
        # Add Vision data if image is captured
        if use_vision and camera_image:
            img = Image.open(camera_image)
            inputs.append(img)
            
        # Add Audio or Text prompt
        if audio_bytes:
            inputs.append({"mime_type": "audio/wav", "data": audio_bytes})
            inputs.append("You are JARVIS. Listen to this audio and respond concisely.")
        else:
            inputs.append(f"You are JARVIS. User says: {user_prompt}. Reply concisely.")

        # GENERATE RESPONSE
        status.info("⚡ Computing...")
        response = model.generate_content(inputs)
        reply = response.text
        
        # DISPLAY
        status.success(f"🤖 {reply}")
        
        # SPEAK
        audio_file = asyncio.run(speak(reply))
        st.audio(audio_file, format='audio/mp3', autoplay=True)

    except Exception as e:
        status.error(f"SYSTEM ERROR: {e}")

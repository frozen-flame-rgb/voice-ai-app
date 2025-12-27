import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
from streamlit_mic_recorder import mic_recorder
from PIL import Image
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JARVIS", page_icon="🤖", layout="centered")

# Hide browser elements
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
    st.error("API Key Missing")
    st.stop()

# --- 2. LOGIC FUNCTIONS ---
def clean_text(text):
    """Removes Markdown symbols so the voice is smooth."""
    clean = re.sub(r'[*#`]', '', text) 
    return clean.strip()

async def speak(text):
    OUTPUT_FILE = "jarvis_reply.mp3"
    spoken_text = clean_text(text)
    communicate = edge_tts.Communicate(spoken_text, "en-GB-RyanNeural")
    await communicate.save(OUTPUT_FILE)
    return OUTPUT_FILE

# --- 3. THE INTERFACE ---
st.markdown("<h1 style='text-align: center; color: #00ffcc; font-family: Courier New;'>J.A.R.V.I.S.</h1>", unsafe_allow_html=True)

# A. CAMERA TOGGLE
use_vision = st.checkbox("👁️ Enable Vision System")

camera_image = None
if use_vision:
    camera_image = st.camera_input("Visual Feed")

# B. VOICE COMMAND
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

# C. NEW SEARCH BAR (Chat Input)
typed_input = st.chat_input("Type your command, Sir...")

# --- 4. EXECUTION ---
# This part triggers if there is EITHER audio input OR typed input
if audio_input or typed_input:
    # Status Indicator
    status = st.empty()
    status.info("⚡ Authenticating...")

    try:
        # Load Model
        model = genai.GenerativeModel("models/gemini-flash-latest")
        
        # PREPARE INPUTS
        inputs = []
        
        # Determine the user's prompt (Audio or Text)
        prompt_text = "You are JARVIS. Be concise."
        
        # Case 1: Handle Vision
        if use_vision and camera_image:
            img = Image.open(camera_image)
            inputs.append(img)

        # Case 2: Handle Audio
        if audio_input:
            inputs.append({"mime_type": "audio/wav", "data": audio_input['bytes']})
            if use_vision and camera_image:
                inputs.append(f"{prompt_text} Analyze this image based on the audio.")
            else:
                inputs.append(f"{prompt_text} Listen to this audio and reply.")
        
        # Case 3: Handle Typing
        elif typed_input:
            if use_vision and camera_image:
                inputs.append(f"{prompt_text} Analyze the image: {typed_input}")
            else:
                inputs.append(f"{prompt_text} Answer this: {typed_input}")

        # GENERATE
        status.info("⚡ Computing...")
        response = model.generate_content(inputs)
        reply = response.text
        
        # DISPLAY & SPEAK
        status.success(f"🤖 {reply}")
        
        # Generate Audio
        audio_file = asyncio.run(speak(reply))
        st.audio(audio_file, format='audio/mp3', autoplay=True)

    except Exception as e:
        status.error(f"ERROR: {e}")

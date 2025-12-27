import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
from streamlit_mic_recorder import mic_recorder
from PIL import Image
import re
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JARVIS", page_icon="🤖", layout="centered")

# Custom JARVIS Styling
st.markdown("""
    <style>
        .stApp {background-color: #000000; color: #00ffcc;}
        .stButton>button {border-radius: 20px; background-color: #003333; color: #00ffcc; border: 1px solid #00ffcc;}
        /* Styling the search bar area */
        .stChatInputContainer {padding-bottom: 20px;}
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
    """Removes Markdown symbols for voice synthesis."""
    return re.sub(r'[*#`]', '', text).strip()

async def speak(text):
    OUTPUT_FILE = "jarvis_reply.mp3"
    spoken_text = clean_text(text)
    communicate = edge_tts.Communicate(spoken_text, "en-GB-RyanNeural")
    await communicate.save(OUTPUT_FILE)
    return OUTPUT_FILE

# --- 3. THE INTERFACE ---
st.markdown("<h1 style='text-align: center; color: #00ffcc; font-family: Courier New;'>J.A.R.V.I.S.</h1>", unsafe_allow_html=True)

# Vision Toggle
use_vision = st.checkbox("👁️ Enable Vision System")
camera_image = st.camera_input("Visual Feed") if use_vision else None

# Voice Component
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    audio_input = mic_recorder(start_prompt="🔴 VOICE COMMAND", stop_prompt="⏹️ STOP", key="recorder", just_once=True)

# Search Bar (Typing Input)
typed_input = st.chat_input("Type your command, Sir...")

# --- 4. EXECUTION ---
if user_prompt:
    status = st.empty()
    status.info("⚡ JARVIS is thinking...")

    try:
        # Use the specific model trained for Image Generation
        # 'gemini-2.5-flash-image' is the stable choice in late 2025
        model = genai.GenerativeModel("gemini-2.5-flash-image")
        
        inputs = []
        if camera_image:
            inputs.append(Image.open(camera_image))
        if audio_bytes:
            # Note: Flash-Image models may prefer text descriptions 
            # for the image part, but can still process audio-to-text.
            inputs.append({"mime_type": "audio/wav", "data": audio_bytes})
        
        # System Instruction
        prompt_prefix = "You are JARVIS. If I ask you to 'create' or 'generate' an image, produce it. Otherwise, answer as a text-based assistant. Command: "
        inputs.append(f"{prompt_prefix}{user_prompt}")

        # GENERATE
        response = model.generate_content(
            inputs,
            generation_config={
                "response_modalities": ["TEXT", "IMAGE"],
                # Optional: Force 16:9 for a "cinematic" JARVIS feel
                # "image_config": {"aspect_ratio": "16:9"} 
            }
        )

        # Handle Multiple Output Parts
        for part in response.candidates[0].content.parts:
            # 1. Handle Text Response
            if hasattr(part, 'text') and part.text:
                st.success(f"🤖 {part.text}")
                audio_file = asyncio.run(speak(part.text))
                st.audio(audio_file, format='audio/mp3', autoplay=True)
            
            # 2. Handle Generated Image
            if hasattr(part, 'inline_data') and part.inline_data:
                img_data = part.inline_data.data
                st.image(img_data, caption="JARVIS Holographic Render", use_container_width=True)

    except Exception as e:
        if "400" in str(e):
            st.error("SYSTEM ERROR: The model is refusing this modality. Try asking: 'Generate an image of...'")
        else:
            status.error(f"SYSTEM ERROR: {e}")

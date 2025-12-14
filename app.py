import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
from streamlit_mic_recorder import mic_recorder
from PIL import Image
import re  # Import Regex for cleaning text

# --- 1. JARVIS CONFIGURATION ---
st.set_page_config(page_title="JARVIS", page_icon="🤖", layout="centered")

# Hide browser elements for App-like feel
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stApp {background-color: #000000; color: #00ffcc;}
        .stButton>button {width: 100%; border-radius: 20px; background-color: #003333; color: #00ffcc; border: 1px solid #00ffcc;}
        .stCameraInput {border: 1px solid #00ffcc; border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

# API Setup
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("SYSTEM ERROR: API KEY MISSING")
    st.stop()

# --- 2. MODEL SETUP ---
if "model" not in st.session_state:
    st.session_state.model = genai.GenerativeModel(
        "models/gemini-flash-latest",
        system_instruction="You are JARVIS. You are precise, technical, and helpful. Address the user as 'Sir'. Keep responses concise (1-2 sentences) for quick voice interaction."
    )

# --- 3. VOICE ENGINE (WITH CLEANER) ---
def clean_text(text):
    """Removes Markdown symbols (*, #, etc.) so the voice doesn't read them."""
    # Remove asterisks, hashes, and backticks
    clean = re.sub(r'[*#`]', '', text) 
    # Remove extra spaces
    clean = clean.strip()
    return clean

async def speak(text):
    OUTPUT_FILE = "jarvis_reply.mp3"
    
    # Clean the text before speaking
    spoken_text = clean_text(text)
    
    # "en-GB-RyanNeural" is the British Butler voice
    communicate = edge_tts.Communicate(spoken_text, "en-GB-RyanNeural")
    await communicate.save(OUTPUT_FILE)
    return OUTPUT_FILE

# --- 4. THE INTERFACE ---
st.markdown("<h1 style='text-align: center; color: #00ffcc; font-family: Courier New;'>J.A.R.V.I.S.</h1>", unsafe_allow_html=True)

# A. VISION SYSTEM
with st.expander("👁️ Vision System", expanded=False):
    camera_input = st.camera_input("Visual Input")

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

# --- 5. EXECUTION ---
if audio_input or camera_input:
    status = st.empty()
    status.info("⚡ Computing...")

    inputs = []
    
    # Handle Vision
    if camera_input:
        img = Image.open(camera_input)
        inputs.append(img)
        inputs.append("Analyze this visual data for the user.")
    
    # Handle Voice
    if audio_input:
        inputs.append({"mime_type": "audio/wav", "data": audio_input['bytes']})
        inputs.append("Listen to this audio and reply. Be extremely concise.")
    elif camera_input and not audio_input:
        inputs.append("Describe what you see briefly.")

    try:
        if inputs:
            # Generate Text
            response = st.session_state.model.generate_content(inputs)
            reply = response.text
            
            # Show Formatted Text (With Bold/Colors) on Screen
            status.success(f"🤖 {reply}")
            
            # Speak Clean Text (No symbols)
            audio_file = asyncio.run(speak(reply))
            st.audio(audio_file, format='audio/mp3', autoplay=True)
        else:
            status.warning("Standby.")

    except Exception as e:
        status.error(f"SYSTEM FAILURE: {e}")

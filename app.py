import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
from streamlit_mic_recorder import mic_recorder
from PIL import Image

# --- 1. JARVIS CONFIGURATION ---
st.set_page_config(page_title="JARVIS", page_icon="🤖", layout="centered")

# Hide all browser elements to look like an App
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stApp {background-color: #000000; color: #00ffcc;}
        h1 {text-align: center; color: #00ffcc; font-family: 'Courier New', Courier, monospace;}
        .stButton>button {width: 100%; border-radius: 20px; background-color: #003333; color: #00ffcc; border: 1px solid #00ffcc;}
    </style>
""", unsafe_allow_html=True)

# API Setup
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("SYSTEM ERROR: API KEY MISSING")
    st.stop()

# --- 2. MODEL SETUP (The Brain) ---
if "model" not in st.session_state:
    # We use Flash for speed. We give it a specific "JARVIS" personality.
    st.session_state.model = genai.GenerativeModel(
        "models/gemini-flash-latest",
        system_instruction="You are JARVIS, a highly advanced AI assistant. You are concise, precise, and efficient. Address the user as 'Sir'. When analyzing images, provide technical and practical solutions."
    )

# --- 3. VOICE ENGINE (The Voice) ---
async def speak(text):
    OUTPUT_FILE = "jarvis_reply.mp3"
    # "en-GB-RyanNeural" sounds like a British Butler (closest to JARVIS)
    communicate = edge_tts.Communicate(text, "en-GB-RyanNeural")
    await communicate.save(OUTPUT_FILE)
    return OUTPUT_FILE

# --- 4. THE INTERFACE ---
st.title("J.A.R.V.I.S.")

# A. THE EYES (Camera Input)
with st.expander("👁️ Activate Vision System", expanded=False):
    camera_input = st.camera_input("Analyze Visual Data")

# B. THE EARS (Voice Input)
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
    # Display Status
    status = st.empty()
    status.info("⚡ Processing Data...")

    # Prepare Inputs
    inputs = []
    
    # Add Camera Image if available
    if camera_input:
        img = Image.open(camera_input)
        inputs.append(img)
        inputs.append("Analyze this visual data and specifically address the following command:")
    
    # Add Audio if available
    if audio_input:
        inputs.append({"mime_type": "audio/wav", "data": audio_input['bytes']})
        inputs.append("Listen to this audio command and execute.")
    elif camera_input and not audio_input:
        inputs.append("Describe what you see and offer technical assistance.")

    # Execute
    try:
        if inputs:
            response = st.session_state.model.generate_content(inputs)
            reply = response.text
            
            # Visual Feedback
            status.success(f"🤖 {reply}")
            
            # Audio Feedback
            audio_file = asyncio.run(speak(reply))
            st.audio(audio_file, format='audio/mp3', autoplay=True)
        else:
            status.warning("Standby Mode. No input detected.")

    except Exception as e:
        status.error(f"SYSTEM FAILURE: {e}")

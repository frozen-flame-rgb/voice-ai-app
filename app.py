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

# --- 2. INITIALIZE SESSION STATE (MEMORY) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. LOGIC FUNCTIONS ---
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

# --- 4. THE INTERFACE ---
st.markdown("<h1 style='text-align: center; color: #00ffcc; font-family: Courier New;'>J.A.R.V.I.S.</h1>", unsafe_allow_html=True)

# A. SETTINGS (Camera & Mic)
with st.expander("⚙️ System Controls", expanded=True):
    c1, c2 = st.columns([1, 1])
    with c1:
        use_vision = st.checkbox("👁️ Enable Vision", value=False)
    with c2:
        # Audio Input
        audio_input = mic_recorder(
            start_prompt="🔴 Speak",
            stop_prompt="⏹️ Stop",
            key="recorder",
            just_once=True,
            use_container_width=True
        )

# Camera Input (Only if enabled)
camera_image = None
if use_vision:
    camera_image = st.camera_input("Visual Feed")

# --- 5. DISPLAY CHAT HISTORY ---
# This loop draws all previous messages every time the app updates
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. HANDLE NEW INPUT ---
# Check if user typed OR spoke
typed_input = st.chat_input("Type your command, Sir...")

user_prompt = None
vision_context = None

# Priority: Audio > Text
if audio_input:
    # We can't transcribe raw bytes easily without an STT model, 
    # so we send the audio directly to Gemini if possible, 
    # OR we treat it as an audio prompt. 
    # For this code, we rely on Gemini to listen to the audio.
    user_prompt = {"mime_type": "audio/wav", "data": audio_input['bytes']}
elif typed_input:
    user_prompt = typed_input

# Execute if we have input
if user_prompt:
    # 1. Display User Message
    with st.chat_message("user"):
        if isinstance(user_prompt, str):
            st.markdown(user_prompt)
        else:
            st.markdown("*🎤 [Audio Command]*")
    
    # 2. Add User Message to History (Text representation)
    if isinstance(user_prompt, str):
        st.session_state.messages.append({"role": "user", "content": user_prompt})
    else:
        st.session_state.messages.append({"role": "user", "content": "*🎤 [Audio Command]*"})

    # 3. Process with Gemini
    try:
        model = genai.GenerativeModel("models/gemini-flash-latest")
        
        # Build the conversation history for the model
        # Note: Gemini Python SDK 'start_chat' is great for text, 
        # but for multimodal (images/audio), list construction is often easier.
        conversation_history = []
        
        # Add system instruction
        conversation_history.append("You are J.A.R.V.I.S. You are helpful, precise, and concise.")
        
        # Add past text interaction context (Simple memory)
        # (We skip heavy images/audio from history to save tokens/complexity for now)
        for msg in st.session_state.messages[-10:]: # Remember last 10 messages
            if msg["role"] == "user":
                conversation_history.append(f"User said: {msg['content']}")
            else:
                conversation_history.append(f"JARVIS said: {msg['content']}")

        # Prepare Current Inputs
        inputs = conversation_history # Start with context
        
        # Add Image if present
        if use_vision and camera_image:
            img = Image.open(camera_image)
            inputs.append(img)
            inputs.append("Analyze this image based on the following command:")

        # Add the User Command (Text or Audio)
        inputs.append(user_prompt)

        # GENERATE
        with st.spinner("⚡ Computing..."):
            response = model.generate_content(inputs)
            reply = response.text

        # 4. Display AI Response
        with st.chat_message("assistant"):
            st.markdown(reply)
        
        # 5. Add AI Response to History
        st.session_state.messages.append({"role": "assistant", "content": reply})

        # 6. Speak Logic
        audio_file = asyncio.run(speak(reply))
        st.audio(audio_file, format='audio/mp3', autoplay=True)

    except Exception as e:
        st.error(f"System Error: {e}")

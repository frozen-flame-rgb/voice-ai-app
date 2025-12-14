import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURATION (Phone UI) ---
st.set_page_config(page_title="Call Gemini", page_icon="📞", layout="centered")

# Hide the Menu and Footer to make it look like an App
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stApp {background-color: #000000; color: white;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# API Setup
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Key missing.")
    st.stop()

# --- 2. MEMORY & MODEL ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "model" not in st.session_state:
    # We use Flash because it is fast and free
    st.session_state.model = genai.GenerativeModel("models/gemini-flash-latest")

# --- 3. VOICE FUNCTIONS ---
async def text_to_speech(text):
    OUTPUT_FILE = "reply.mp3"
    # "en-US-AriaNeural" is the best "AI Assistant" voice
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
    await communicate.save(OUTPUT_FILE)
    return OUTPUT_FILE

# --- 4. THE PHONE INTERFACE ---
st.markdown("<h2 style='text-align: center;'>📞 Gemini Voice</h2>", unsafe_allow_html=True)
st.write("---")

# THE BIG BUTTON (This is the only thing you touch)
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    # This records your voice
    audio_input = mic_recorder(
        start_prompt="🔴 Tap to Speak",
        stop_prompt="⏹️ Sending...",
        key="recorder",
        just_once=True,
        use_container_width=True
    )

# --- 5. INTELLIGENT PROCESSING ---
if audio_input:
    # A. Display what you just said (Optional visual)
    st.info("🎤 Message sent...")

    # B. Build the Memory Context
    # We take the last 5 messages so it remembers context but stays fast
    history_context = ""
    for msg in st.session_state.chat_history[-5:]:
        history_context += f"{msg['role']}: {msg['content']}\n"
    
    # C. Send to Gemini
    # We tell Gemini: "Here is the history, and here is the new audio."
    try:
        model = st.session_state.model
        prompt = f"""
        You are currently on a phone call with the user. 
        Previous conversation:
        {history_context}
        
        Instruction: Listen to the attached audio and reply naturally as if on a call. 
        Keep your answer short (1-2 sentences) so the conversation flows fast.
        """
        
        response = model.generate_content([
            prompt,
            {"mime_type": "audio/wav", "data": audio_input['bytes']}
        ])
        
        ai_reply = response.text

        # D. Save to Memory
        st.session_state.chat_history.append({"role": "User", "content": "(Voice Audio)"})
        st.session_state.chat_history.append({"role": "AI", "content": ai_reply})

        # E. TALK BACK (Auto-Play)
        # This makes the AI speak immediately without you clicking "Play"
        audio_file = asyncio.run(text_to_speech(ai_reply))
        st.audio(audio_file, format='audio/mp3', autoplay=True)
        
        st.success(f"🗣️ {ai_reply}")

    except Exception as e:
        st.error(f"Call dropped: {e}")

# Show Memory (Small at the bottom)
with st.expander("📝 Call History"):
    for msg in st.session_state.chat_history:
        st.write(f"**{msg['role']}**: {msg['content']}")







import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder

# 1. SETUP
st.set_page_config(page_title="My AI", page_icon="🎙️")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Key missing. Please set it in Streamlit Secrets.")
    st.stop()

# 2. LOGIC
def text_to_speech(text):
    try:
        tts = gTTS(text=text, lang='en')
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except:
        return None

# 3. INTERFACE
st.title("🎙️ My Voice AI")

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. INPUTS
st.write("---")
col1, col2 = st.columns([3, 1])

with col1:
    text_input = st.chat_input("Type here...")

with col2:
    st.write("Tap to Speak:")
    audio_input = mic_recorder(start_prompt="🎤", stop_prompt="⏹️", key="recorder")

# 5. PROCESSING
prompt = None
if text_input:
    prompt = text_input
elif audio_input:
    prompt = "I am sending you a voice message. Please listen to it."

if prompt:
    # Show User Input
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if audio_input:
            st.audio(audio_input['bytes'])

    # Get AI Response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                model = genai.GenerativeModel("gemini-pro")
                
                # Build Payload
                content = []
                if audio_input:
                    content.append({"mime_type": "audio/wav", "data": audio_input['bytes']})
                    content.append("Listen to this audio and answer concisely.")
                else:
                    content.append(prompt)

                response = model.generate_content(content)
                
                # Show Text
                st.markdown(response.text)
                
                # Play Audio
                audio_bytes = text_to_speech(response.text)
                if audio_bytes:
                    st.audio(audio_bytes, format='audio/mp3', start_time=0)

                st.session_state.messages.append({"role": "model", "content": response.text})
            
            except Exception as e:

                st.error(f"Error: {e}")





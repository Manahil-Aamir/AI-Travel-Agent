import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import tempfile
import os
import threading
from config import THEME

def speak(text):
    def play_audio():
        try:
            tts = gTTS(text)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
                tts.save(tmpfile.name)
                st.audio(tmpfile.name, format="audio/mp3")
        except Exception as e:
            st.warning(f"🔇 Voice error: {e}")

    if "speak_response" in st.session_state and st.session_state.speak_response:
        thread = threading.Thread(target=play_audio)
        thread.start()
        st.session_state.speak_response = False

def recognize_speech():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.info("🎙️ Listening... Speak now.")
            audio = r.listen(source)
            text = r.recognize_google(audio)
            return text
    except sr.UnknownValueError:
        return "Sorry, I didn't understand that."
    except sr.RequestError:
        return "Speech service unavailable."
    except Exception as e:
        return f"Microphone error: {str(e)}"

def voice_interface():
    if "voice_active" in st.session_state and st.session_state.voice_active:
        user_input = recognize_speech()
        if user_input:
            st.session_state.voice_input = user_input
            st.session_state.voice_active = False
            st.experimental_rerun()

    if "voice_input" in st.session_state:
        st.markdown(f"""
        <div style='background-color: {THEME.get("card_bg", "#f9f9f9")}; padding: 1rem; border-radius: 0.5rem;'>
            <h4>🎤 You said:</h4>
            <p>{st.session_state.voice_input}</p>
        </div>
        """, unsafe_allow_html=True)
        return st.session_state.voice_input

    return None

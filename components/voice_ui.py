# Voice interface components
import streamlit as st
import speech_recognition as sr
import pyttsx3
import threading
from config import THEME

# Initialize voice engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.8)

def speak(text):
    def speak_thread():
        engine.say(text)
        engine.runAndWait()
    
    if "speak_response" in st.session_state and st.session_state.speak_response:
        thread = threading.Thread(target=speak_thread)
        thread.start()
        st.session_state.speak_response = False

def recognize_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Speak now!")
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Sorry, I didn't understand that."
        except sr.RequestError:
            return "Sorry, my speech service is down."

def voice_interface():
    if "voice_active" in st.session_state and st.session_state.voice_active:
        user_input = recognize_speech()
        if user_input:
            st.session_state.voice_input = user_input
            st.session_state.voice_active = False
            st.experimental_rerun()
    
    if "voice_input" in st.session_state:
        st.markdown(f"""
        <div class="modern-card">
            <h4>🎤 You said:</h4>
            <p>{st.session_state.voice_input}</p>
        </div>
        """, unsafe_allow_html=True)
        return st.session_state.voice_input
    return None
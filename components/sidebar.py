# Sidebar navigation
import streamlit as st
from config import THEME

def create_sidebar():
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2065/2065067.png", width=80)
        st.title("Voyager AI")
        st.markdown("Your intelligent travel companion")
        
        st.markdown("---")
        
        # Navigation
        st.subheader("Navigation")
        nav_options = {
            "🏠 Dashboard": "dashboard",
            "✨ Recommendations": "recommendations",
            "✈️ Flights": "flights",
            "🏨 Hotels": "hotels",
            "🛒 Shopping": "shopping",
            "🍽️ Restaurants": "restaurants",
            "💬 Chat": "chat"
        }
        
        selected = st.radio(
            "Go to",
            list(nav_options.keys()),
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Voice Assistant Section
        st.subheader("Voice Assistant")
        voice_col1, voice_col2 = st.columns(2)
        with voice_col1:
            if st.button("🎤 Speak", key="voice_btn"):
                st.session_state.voice_active = True
        with voice_col2:
            if st.button("🔊 Hear", key="hear_btn"):
                if "last_response" in st.session_state:
                    st.session_state.speak_response = True
        
        st.markdown("---")
        
        # User Profile
        st.subheader("Profile")
        if "user_name" not in st.session_state:
            st.session_state.user_name = "Guest"
        st.write(f"Welcome, {st.session_state.user_name}!")
        
        return nav_options[selected]
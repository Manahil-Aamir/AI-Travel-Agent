# Chat interface
import streamlit as st
import json
from groq import Groq
from datetime import datetime
from components.ui_utils import modern_card
from components.voice_ui import speak
from config import GROQ_API_KEY, THEME

def chat_tab(voice_input=None):
    st.header("💬 Travel Chat Assistant")
    
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
    
    # Voice input handling
    if voice_input:
        process_user_input(voice_input)
    
    # Text input
    user_input = st.text_input("Ask me anything about travel...", key="chat_input")
    if st.button("Send", key="send_chat"):
        if user_input.strip():
            process_user_input(user_input)
    
    # Display conversation
    for msg in st.session_state.conversation:
        if msg['role'] == 'user':
            modern_card("You", msg['content'], "👤")
        else:
            modern_card("Travel Assistant", msg['content'], "🤖")
    
    # Clear conversation button
    if st.button("Clear Conversation", key="clear_chat"):
        st.session_state.conversation = []
        st.experimental_rerun()

def process_user_input(user_input):
    client = Groq(api_key=GROQ_API_KEY)
    
    # Add user message to conversation
    st.session_state.conversation.append({
        'role': 'user',
        'content': user_input,
        'timestamp': datetime.now().isoformat()
    })
    
    # Generate response
    with st.spinner("Thinking..."):
        try:
            response = client.chat.completions.create(
                messages=[{"role": m['role'], "content": m['content']} 
                         for m in st.session_state.conversation] + [
                    {
                        "role": "system",
                        "content": """You are a helpful travel assistant. Provide concise, 
                        informative answers about travel destinations, flights, hotels, 
                        packing tips, and general travel advice."""
                    }
                ],
                model="llama3-8b-8192",
                temperature=0.7
            )
            
            assistant_response = response.choices[0].message.content
            
            # Add assistant response to conversation
            st.session_state.conversation.append({
                'role': 'assistant',
                'content': assistant_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Set the response to be spoken
            st.session_state.last_response = assistant_response
            st.session_state.speak_response = True
            
            st.experimental_rerun()
            
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
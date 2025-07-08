import streamlit as st
from datetime import datetime
from neo4j import GraphDatabase
from groq import Groq
from config import GROQ_API_KEY, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

import speech_recognition as sr
import pyttsx4
import time

# ========== Voice Engine Setup ==========
def speak(text):
    """Speak text with fresh engine instance"""
    try:
        engine = pyttsx4.init()
        engine.say(text)
        engine.runAndWait()
        del engine
        st.info(f"🔊 Assistant says: {text}")
    except Exception:
        print(Exception)
        print("Error initializing text-to-speech engine. Using Streamlit's info message instead.")
        
        st.info(f"🔊 Assistant says: {text}")

def listen_once():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 4000
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            st.success("🎤 Listening now... Speak clearly!")
            audio = recognizer.listen(source, timeout=45, phrase_time_limit=50)
        text = recognizer.recognize_google(audio)
        st.success(f"✅ You said: '{text}'")
        return text
    except sr.WaitTimeoutError:
        return None
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        st.error(f"🚫 Speech recognition service error: {e}")
        return None
    except Exception as e:
        st.error(f"🚫 Microphone error: {e}")
        return None

# ========== Neo4j ==========
def store_conversation(user_id, message, response):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            session.run("""
                MERGE (u:User {id: $user_id})
                CREATE (m:Message {text: $message, timestamp: datetime()})
                CREATE (r:Response {text: $response, timestamp: datetime()})
                CREATE (u)-[:SENT]->(m)
                CREATE (m)-[:GENERATED]->(r)
            """, user_id=user_id, message=message, response=response)
    except Exception:
        pass
    finally:
        driver.close()

# ========== Process Message ==========
def process_message(message):
    client = Groq(api_key=GROQ_API_KEY)

    # Add user message
    st.session_state.conversation.append({
        'role': 'user',
        'content': message,
        'timestamp': datetime.now().isoformat()
    })

    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": message}],
            model="llama3-8b-8192"
        )
        assistant_response = response.choices[0].message.content

        store_conversation(
            st.session_state.user_id,
            message,
            assistant_response
        )

        st.session_state.conversation.append({
            'role': 'assistant',
            'content': assistant_response,
            'timestamp': datetime.now().isoformat()
        })

        # ✅ Speak only if voice mode is active
        if st.session_state.get("voice_mode_active", False):
            print(f"voice mode active, speaking response: {assistant_response}")
            speak(assistant_response)

        return assistant_response

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# ========== Voice Conversation Loop ==========
def start_voice_conversation():
    if len(st.session_state.conversation) == 0:
        greeting = "Hello! I'm your travel assistant. How can I help you today?"
        st.session_state.conversation.append({
            'role': 'assistant',
            'content': greeting,
            'timestamp': datetime.now().isoformat()
        })
        speak(greeting)

    st.session_state.should_listen = True

def voice_listening_cycle():
    if not st.session_state.voice_mode_active or not st.session_state.should_listen:
        return

    user_input = listen_once()

    if user_input:
        if user_input.strip():
            with st.spinner("🤖 Generating response..."):
                assistant_response = process_message(user_input)

            if assistant_response:
                time.sleep(2)
                st.experimental_rerun()
        else:
            time.sleep(2)
            st.experimental_rerun()
    elif user_input is None:
        time.sleep(1)
        st.experimental_rerun()
    else:
        time.sleep(2)
        st.experimental_rerun()

# ========== Main Chat ==========
def chat_tab():
    st.header("💬 Travel Chat Assistant")

    if "user_id" not in st.session_state:
        st.session_state.user_id = "user_001"
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
    if "voice_mode_active" not in st.session_state:
        st.session_state.voice_mode_active = False
    if "should_listen" not in st.session_state:
        st.session_state.should_listen = False

    voice_mode_on = st.toggle("📞 Voice Mode (Phone Call Style)", value=st.session_state.voice_mode_active)

    if voice_mode_on != st.session_state.voice_mode_active:
        st.session_state.voice_mode_active = voice_mode_on

        if voice_mode_on:
            st.success("📞 Voice mode activated! Starting phone-style conversation...")
            start_voice_conversation()
        else:
            st.info("📞 Voice mode deactivated")
            st.session_state.should_listen = False

    if st.session_state.voice_mode_active and st.session_state.should_listen:
        voice_listening_cycle()

    if st.session_state.voice_mode_active:
        st.markdown("### 📞 **Phone Call Mode Active**")
        st.markdown("- 🎤 **Microphone Status**: Ready")
        st.markdown("- 🔊 **Speech Output**: Enabled") 
        st.markdown("- 📱 **Mode**: Continuous listening")
        st.markdown("- ⚠️ **Important**: Make sure your microphone is working and permitted")

        if st.button("🔧 Test Microphone"):
            st.info("Testing microphone... Please say something")
            test_input = listen_once()
            if test_input:
                st.success(f"✅ Microphone working! Heard: '{test_input}'")
            else:
                st.error("❌ Microphone test failed. Check permissions and try again.")
    else:
        st.subheader("⌨️ Text Input")
        user_input = st.text_input("Ask about travel...", key="chat_input")
        if st.button("Send"):
            if user_input.strip():
                assistant_response = process_message(user_input)
                if assistant_response:
                    st.experimental_rerun()

    st.subheader("📜 Conversation History")
    if st.session_state.conversation:
        for msg in st.session_state.conversation:
            if msg['role'] == 'user':
                st.markdown(f"**🧑 You:** {msg['content']}")
            else:
                st.markdown(f"**🤖 Assistant:** {msg['content']}")
    else:
        st.info("No conversation yet. Toggle voice mode or type a message to start!")

    st.sidebar.markdown("""
    ## 📞 Phone Call Mode

    **When Voice Mode is ON:**
    - Works like a phone call
    - Assistant listens continuously
    - Speak naturally when prompted
    - Assistant responds with voice
    - All messages appear on screen
    - Toggle off to end the call

    **When Voice Mode is OFF:**
    - Use text input to chat
    - Type your questions normally
    - No voice interaction

    ### Tips:
    - Speak clearly and at normal pace
    - Wait for assistant to finish speaking
    - Short pauses are okay
    - Toggle off anytime to stop
    """)

    if st.session_state.voice_mode_active:
        time.sleep(0.5)
        st.experimental_rerun()

# Run the app
if __name__ == "__main__":
    chat_tab()

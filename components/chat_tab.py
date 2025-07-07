import streamlit as st
from datetime import datetime
from neo4j import GraphDatabase
from groq import Groq
from config import GROQ_API_KEY, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

def store_conversation(user_id, message, response):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            session.run("""
            MERGE (u:User {id: $user_id})
            CREATE (m:Message {
                text: $message,
                timestamp: datetime()
            })
            CREATE (r:Response {
                text: $response,
                timestamp: datetime()
            })
            CREATE (u)-[:SENT]->(m)
            CREATE (m)-[:GENERATED]->(r)
            """, 
            user_id=user_id, message=message, response=response)
    except Exception as e:
        st.error(f"Failed to save conversation: {str(e)}")
    finally:
        driver.close()

def chat_tab(voice_input=None):
    st.header("💬 Travel Chat Assistant")
    
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
    
    # Process voice input
    if voice_input:
        process_message(voice_input)
    
    # Text input
    user_input = st.text_input("Ask about travel...", key="chat_input")
    if st.button("Send"):
        if user_input.strip():
            process_message(user_input)
    
    # Display conversation
    for msg in st.session_state.conversation:
        if msg['role'] == 'user':
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Assistant:** {msg['content']}")

def process_message(message):
    client = Groq(api_key=GROQ_API_KEY)
    
    # Add to conversation
    st.session_state.conversation.append({
        'role': 'user',
        'content': message,
        'timestamp': datetime.now().isoformat()
    })
    
    # Generate response
    with st.spinner("Thinking..."):
        try:
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": message}],
                model="llama3-8b-8192"
            )
            assistant_response = response.choices[0].message.content
            
            # Store in Neo4j
            store_conversation(
                st.session_state.user_id,
                message,
                assistant_response
            )
            
            # Add to conversation
            st.session_state.conversation.append({
                'role': 'assistant',
                'content': assistant_response,
                'timestamp': datetime.now().isoformat()
            })
            
            st.experimental_rerun()
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
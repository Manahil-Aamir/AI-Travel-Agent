# Conversation agent
from fetchai.ledger.api import LedgerApi
from fetchai.ledger.contract import Contract
from fetchai.ledger.crypto import Entity
from groq import Groq
from config import GROQ_API_KEY

class ChatAgent:
    def __init__(self, entity: Entity, contract: Contract):
        self.entity = entity
        self.contract = contract
        self.api = LedgerApi('127.0.0.1', 8000)
        self.groq_client = Groq(api_key=GROQ_API_KEY)
    
    def process_message(self, message, conversation_history=[]):
        """Process user message and generate response"""
        # Store message on blockchain
        self.contract.action(
            self.api, 'storeMessage',
            self.entity, message=message
        )
        
        # Generate response using Groq
        response = self.groq_client.chat.completions.create(
            messages=conversation_history + [
                {
                    "role": "system",
                    "content": "You are a helpful travel assistant."
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            model="llama3-8b-8192"
        )
        
        assistant_response = response.choices[0].message.content
        
        # Store response on blockchain
        self.contract.action(
            self.api, 'storeResponse',
            self.entity, message_id="latest", 
            response=assistant_response
        )
        
        return assistant_response
    
    def get_conversation_history(self, user_id):
        """Retrieve conversation history from blockchain"""
        query = self.contract.query(
            self.api, 'getConversation',
            user_id=user_id
        )
        return query
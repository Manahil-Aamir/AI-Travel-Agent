import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
LOCATIONIQ_API_KEY = os.getenv("LOCATIONIQ_API_KEY")
SPOONACULAR_KEY = os.getenv("SPOONACULAR_API_KEY")
FETCH_AI_API_KEY = os.getenv("FETCH_AI_API_KEY")

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Fetch.ai Agents Configuration
FETCH_AGENTS = {
    "flight": os.getenv("FETCH_FLIGHT_AGENT_ID"),
    "hotel": os.getenv("FETCH_HOTEL_AGENT_ID"),
    "shopping": os.getenv("FETCH_SHOPPING_AGENT_ID"),
    "chat": os.getenv("FETCH_CHAT_AGENT_ID")
}

# UI Constants
THEME = {
    "primary": "#6C63FF",
    "secondary": "#FF6584",
    "accent": "#36D1DC",
    "dark": "#121826",
    "light": "#F8F9FC",
    "card_bg": "rgba(255, 255, 255, 0.95)",
    "card_border": "rgba(108, 99, 255, 0.2)"
}

# App Settings
DEFAULT_LOCATION = "San Francisco"
DEFAULT_CURRENCY = "USD"
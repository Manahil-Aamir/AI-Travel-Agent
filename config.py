import os
from dotenv import load_dotenv

# Load .env only if needed
load_dotenv()

# Try to import Streamlit and check if secrets are available
try:
    import streamlit as st
    _secrets_available = hasattr(st, "secrets") and len(st.secrets) > 0
except ImportError:
    st = None
    _secrets_available = False

def get_secret(key, default=None):
    if _secrets_available and key in st.secrets:
        return st.secrets[key]
    return os.getenv(key, default)

# =======================
# API Keys & Configs
# =======================

GROQ_API_KEY = get_secret("GROQ_API_KEY")
TAVILY_API_KEY = get_secret("TAVILY_API_KEY")
RAPIDAPI_KEY = get_secret("RAPIDAPI_KEY")
LOCATIONIQ_API_KEY = get_secret("LOCATIONIQ_API_KEY")
SPOONACULAR_KEY = get_secret("SPOONACULAR_API_KEY")
FETCH_AI_API_KEY = get_secret("FETCH_AI_API_KEY")

# Neo4j Configuration
NEO4J_URI = get_secret("NEO4J_URI")
NEO4J_USERNAME = get_secret("NEO4J_USERNAME")
NEO4J_PASSWORD = get_secret("NEO4J_PASSWORD")

# Fetch Agents
FETCH_AGENTS = {
    "flight": get_secret("FETCH_FLIGHT_AGENT_ID"),
    "hotel": get_secret("FETCH_HOTEL_AGENT_ID"),
    "shopping": get_secret("FETCH_SHOPPING_AGENT_ID"),
    "chat": get_secret("FETCH_CHAT_AGENT_ID")
}

# =======================
# UI Constants & Defaults
# =======================

THEME = {
    "primary": "#6C63FF",
    "secondary": "#FF6584",
    "accent": "#36D1DC",
    "dark": "#121826",
    "light": "#F8F9FC",
    "card_bg": "rgba(255, 255, 255, 0.95)",
    "card_border": "rgba(108, 99, 255, 0.2)"
}

DEFAULT_LOCATION = "San Francisco"
DEFAULT_CURRENCY = "USD"

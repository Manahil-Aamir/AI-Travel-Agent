# Main app integration
import streamlit as st
from components.recommendations_tab import recommendations_tab
from components.sidebar import create_sidebar
from components.voice_ui import voice_interface, speak
from components.ui_utils import set_custom_theme, modern_card
from components.flight_tab import flight_tab
from components.hotel_tab import hotel_tab
from components.shopping_tab import shopping_tab
from components.recipe_tab import restaurant_tab
from components.chat_tab import chat_tab

from config import THEME  # Removed unused import

# Initialize session state
def init_session_state():
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
    if "flights" not in st.session_state:
        st.session_state.flights = []
    if "hotels" not in st.session_state:
        st.session_state.hotels = []
    if "products" not in st.session_state:
        st.session_state.products = []
    if "recipes" not in st.session_state:
        st.session_state.recipes = []

def main():
    # Set up UI
    st.set_page_config(layout="wide", page_title="Voyager AI", page_icon="🌍")
    set_custom_theme()
    
    
    # Initialize session state
    init_session_state()
    
    # Create sidebar and get selected tab
    selected_tab = create_sidebar()
    
    # Main content area
    st.title("🌍 Voyager AI Travel Assistant")
    
    # Voice interface (always available)
    voice_input = voice_interface()
    
    # Handle tab content
    if selected_tab == "dashboard":
        dashboard_tab()
    elif selected_tab == "flights":
        flight_tab()
    elif selected_tab == "hotels":
        hotel_tab()
    elif selected_tab == "shopping":
        shopping_tab(voice_input)
    elif selected_tab == "recommendations":
        recommendations_tab()  # Pass voice_input if recommendations_tab expects it, or remove parentheses if it's a module
    elif selected_tab == "restaurants":
        restaurant_tab()
    elif selected_tab == "chat":
        chat_tab()
    
    # Handle voice response
    if "last_response" in st.session_state and "speak_response" in st.session_state:
        speak(st.session_state.last_response)

def dashboard_tab():
    modern_card(
        "Welcome to Voyager AI",
        "Your intelligent travel assistant that helps you plan trips, find flights, book hotels, shop for travel gear, and more!",
        "🌟"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        modern_card(
            "Quick Actions",
            """
            - ✈️ Search flights
            - 🏨 Find hotels
            - 🛒 Shop for travel gear
            - 🍽️ Discover restaurants
            """,
            "⚡"
        )
    
    with col2:
        modern_card(
            "Recent Searches",
            """
            - New York to Paris (Oct 26)
            - Hotels in San Francisco
            - Travel backpacks
            - Italian restaurants
            """,
            "🕒"
        )
    
    modern_card(
        "Travel Inspiration",
        """
        - 🌴 Bali, Indonesia - Tropical paradise
        - 🏛️ Rome, Italy - Historic wonders
        - 🗼 Tokyo, Japan - Modern metropolis
        - 🏔️ Swiss Alps - Mountain retreat
        """,
        "✨"
    )

if __name__ == "__main__":
    main()
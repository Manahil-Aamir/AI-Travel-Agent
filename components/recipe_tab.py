import streamlit as st
import requests
from components.ui_utils import modern_card
from config import RAPIDAPI_KEY

def restaurant_tab(voice_input=None):
    st.header("🍽️ Restaurant Finder")
    
    if voice_input:
        modern_card("Voice Input", f"You said: {voice_input}", "🎤")
    
    restaurant_query = st.text_input("Find restaurants in (city or location)", "New York")
    cuisine_query = st.text_input("Cuisine (optional)", "Italian")
    
    if st.button("Search Restaurants", key="restaurant_search"):
        with st.spinner("Finding restaurants..."):
            restaurants = search_restaurants(restaurant_query, cuisine_query)
            st.session_state.restaurants = restaurants
            
            if restaurants:
                st.success(f"Found {len(restaurants)} restaurants")
                display_restaurants(restaurants)
            else:
                st.warning("No restaurants found")

def search_restaurants(location, cuisine=""):
    url = "https://yelp-business-api.p.rapidapi.com/search/category"
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "yelp-business-api.p.rapidapi.com"
    }
    
    params = {
        "location": location,
        "search_category": "restaurants",
        "limit": "5",
        "offset": "0",
        "business_details_type": "basic"
    }
    
    if cuisine:
        params["search_term"] = cuisine
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        # Debugging information
        st.write(f"API Request: {response.request.method} {response.request.url}")
        st.write(f"Headers: {response.request.headers}")
        st.write(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            return data.get('business_search_result', [])
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        st.error(f"Restaurant search error: {str(e)}")
        return []

def display_restaurants(restaurants):
    for rest in restaurants:
        # Extract address information
        address_parts = []
        if rest.get('address1'):
            address_parts.append(rest['address1'])
        if rest.get('city'):
            address_parts.append(rest['city'])
        if rest.get('state'):
            address_parts.append(rest['state'])
        if rest.get('zip'):
            address_parts.append(rest['zip'])
        
        # Extract categories
        categories = []
        for cat in rest.get('categories', []):
            if isinstance(cat, dict) and 'name' in cat:
                categories.append(cat['name'])
        
        modern_card(
            rest.get('name', 'Unknown Restaurant'),
            f"""
            ⭐ **Rating:** {rest.get('avg_rating', 'N/A')} ({rest.get('review_count', 'N/A')} reviews)
            📍 **Address:** {', '.join(address_parts) if address_parts else 'Address not available'}
            🍽️ **Categories:** {', '.join(categories) if categories else 'Not specified'}
            📞 **Phone:** {rest.get('localized_phone', 'Not available')}
            🔗 [More Info](#)
            """,
            "🍽️"
        )
# Recipe functionality
import streamlit as st
import requests
from components.ui_utils import modern_card
from config import SPOONACULAR_KEY, RAPIDAPI_KEY, THEME

def recipe_tab(voice_input=None):
    st.header("🍽️ Restaurants & Recipes")
    
    if voice_input:
        modern_card("Voice Input", f"You said: {voice_input}", "🎤")
    
    tab1, tab2 = st.tabs(["🍳 Recipes", "🍽️ Restaurants"])
    
    with tab1:
        recipe_query = st.text_input("What would you like to cook?", "pasta")
        
        if st.button("Search Recipes", key="recipe_search"):
            with st.spinner("Finding recipes..."):
                recipes = search_recipes(recipe_query)
                st.session_state.recipes = recipes
                
                if recipes:
                    st.success(f"Found {len(recipes)} recipes")
                    display_recipes(recipes)
                else:
                    st.warning("No recipes found")
    
    with tab2:
        restaurant_query = st.text_input("Find restaurants in (city or location)", "San Francisco")
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

def search_recipes(query):
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": SPOONACULAR_KEY,
        "query": query,
        "number": 5,
        "instructionsRequired": True
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('results', [])
    except Exception as e:
        st.error(f"Recipe search error: {str(e)}")
    return []

def display_recipes(recipes):
    for recipe in recipes:
        modern_card(
            recipe.get('title', 'No title'),
            f"""
            ⏱️ **Ready in:** {recipe.get('readyInMinutes', 'N/A')} minutes  
            👨‍🍳 **Servings:** {recipe.get('servings', 'N/A')}  
            <img src="{recipe.get('image', '')}" width="100%">  
            🔗 [View Recipe](#)
            """,
            "🍳"
        )

def search_restaurants(location, cuisine=""):
    url = "https://yelp-com.p.rapidapi.com/businesses/search"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "yelp-com.p.rapidapi.com"
    }
    params = {
        "location": location,
        "term": cuisine if cuisine else "restaurant",
        "limit": "5",
        "sort_by": "rating"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get('businesses', [])
    except Exception as e:
        st.error(f"Restaurant search error: {str(e)}")
    return []

def display_restaurants(restaurants):
    for rest in restaurants:
        modern_card(
            rest.get('name', 'Unknown'),
            f"""
            ⭐ **Rating:** {rest.get('rating', 'N/A')} ({rest.get('review_count', 'N/A')} reviews)  
            📍 **Address:** {', '.join(rest.get('location', {}).get('display_address', []))}  
            🍽️ **Cuisine:** {', '.join([c.get('title', '') for c in rest.get('categories', [])])}  
            🔗 [View on Yelp]({rest.get('url', '#')})
            """,
            "🍽️"
        )
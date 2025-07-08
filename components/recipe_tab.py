import os
import requests
import streamlit as st
import html2text
from groq import Groq
from neo4j import GraphDatabase
from components.ui_utils import modern_card
from config import RAPIDAPI_KEY, GROQ_API_KEY, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from webbrowser import open as web
from bs4 import BeautifulSoup

# Initialize AI client
groq = Groq(api_key=GROQ_API_KEY)

def store_restaurant_interaction(user_id, restaurant_id, action):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            session.run("""
                MERGE (u:User {id: $user_id})
                MERGE (r:Restaurant {id: $restaurant_id})
                CREATE (u)-[:VIEWED {action: $action, timestamp: datetime()}]->(r)
            """, user_id=user_id, restaurant_id=restaurant_id, action=action)
    except Exception as e:
        st.error(f"Failed to save interaction: {e}")
    finally:
        driver.close()

def restaurant_tab():
    st.header("🍽️ Restaurant Finder & Menu Assistant")

    # Initialize session state for menu displays
    if 'menu_displays' not in st.session_state:
        st.session_state.menu_displays = {}

    city = st.text_input("City or Location", "New York")
    cuisine = st.text_input("Cuisine (optional)", "Italian")

    if st.button("Find Restaurants"):
        with st.spinner("Searching..."):
            restaurants = search_restaurants(city, cuisine)
            st.session_state.restaurants = restaurants
            # Clear previous menu displays when searching new restaurants
            st.session_state.menu_displays = {}
            
            if restaurants:
                st.success(f"Found {len(restaurants)} restaurants")
            else:
                st.warning("No restaurants found")

    # Display restaurants if they exist in session state
    if hasattr(st.session_state, 'restaurants') and st.session_state.restaurants:
        display_restaurants(st.session_state.restaurants)

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

    resp = requests.get(url, headers=headers, params=params)
    return resp.json().get("business_search_result", []) if resp.status_code == 200 else []

def display_restaurants(restaurants):
    for i, r in enumerate(restaurants):
        rid = r.get("id", f"restaurant_{i}")
        
        # Create a container for each restaurant
        with st.container():
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if r.get("photo_url"):
                    st.image(r["photo_url"], width=150)
                else:
                    st.write("📸 No image")

            with col2:
                st.subheader(r.get("name", "Unknown"))
                parts = [r.get(k, "") for k in ("address1","city","state","zip") if r.get(k)]
                st.caption(", ".join(parts) or "Address not available")

                st.write(f"⭐ {r.get('avg_rating', 'N/A')} · {r.get('review_count', 0)} reviews")
                cats = ", ".join(c.get("name", "") for c in r.get("categories", []) if isinstance(c, dict))
                st.write(f"🍽️ {cats or 'Not specified'}")

                # Store user interaction
                if "user_id" in st.session_state:
                    store_restaurant_interaction(st.session_state.user_id, rid, "viewed")

                # Menu button with unique key
                menu_button_key = f"menu_btn_{rid}"
                if st.button("View Menu", key=menu_button_key):
                    # Toggle menu display for this specific restaurant
                    st.session_state.menu_displays[rid] = not st.session_state.menu_displays.get(rid, False)
                    st.rerun()

            # Show menu summary only for this restaurant if requested
            if st.session_state.menu_displays.get(rid, False):
                with st.container():
                    st.markdown("#### Menu Summary")
                    
                    # Check if we already have the menu analysis cached
                    menu_cache_key = f"menu_analysis_{rid}"
                    if menu_cache_key not in st.session_state:
                        with st.spinner("Fetching menu analysis..."):
                            summary = analyze_menu_with_groq(r.get("name", ""), r.get("url", ""))
                            st.session_state[menu_cache_key] = summary
                    
                    st.write(st.session_state[menu_cache_key])
                    
                    # Add a button to hide the menu
                    hide_button_key = f"hide_menu_{rid}"
                    if st.button("Hide Menu", key=hide_button_key):
                        st.session_state.menu_displays[rid] = False
                        st.rerun()

            st.divider()
def get_duckduckgo_menu_url(restaurant_name):
    """Search for restaurant menu URL using DuckDuckGo"""
    query = f"{restaurant_name} menu"
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        results = soup.find_all("a", class_="result__a", href=True)
        if results:
            return results[0]["href"]
    except Exception as e:
        st.error(f"Error searching for menu: {e}")
        return None

    return None

def analyze_menu_by_name(restaurant_name):
    """Analyze restaurant menu by searching for it online"""
    menu_url = get_duckduckgo_menu_url(restaurant_name)
    if not menu_url:
        return "⚠️ Could not find a menu link online for this restaurant."

    try:
        response = requests.get(menu_url, timeout=10)
        response.raise_for_status()

        md = html2text.HTML2Text()
        md.ignore_links = True
        md.ignore_images = True
        menu_md = md.handle(response.text)[:8000]

        ai_resp = groq.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "You are a food expert. Analyze a restaurant menu and provide a concise summary of key dishes, specialties, and highlights. Focus on popular items and unique offerings."
                },
                {
                    "role": "user", 
                    "content": f"Menu content for {restaurant_name}:\n\n{menu_md}"
                }
            ],
            model="llama3-70b-8192",
            temperature=0.7,
            max_tokens=500
        )
        return ai_resp.choices[0].message.content + f"\n\n[View Source]({menu_url})"

    except Exception as e:
        return f"❌ Error analyzing menu: {e}"

def analyze_menu_with_groq(name, url):
    """Fallback method - try restaurant URL first, then search online"""
    # First try the restaurant's own website
    if url:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            
            md_converter = html2text.HTML2Text()
            md_converter.ignore_links = True
            md_converter.ignore_images = True
            menu_md = md_converter.handle(resp.text)[:8000]

            # Check if the content looks like it might contain menu information
            if any(word in menu_md.lower() for word in ['menu', 'appetizer', 'entree', 'dessert', 'pizza', 'burger', 'salad', 'soup', 'price', '$']):
                ai_resp = groq.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a food expert. Analyze a restaurant menu and provide a concise summary of key dishes, specialties, and highlights. Focus on popular items and unique offerings."
                        },
                        {
                            "role": "user",
                            "content": f"Here is the menu content for {name}:\n\n{menu_md}"
                        }
                    ],
                    model="llama3-70b-8192",
                    temperature=0.7,
                    max_tokens=500
                )
                return ai_resp.choices[0].message.content + f"\n\n[View Source]({url})"
        except Exception:
            pass  # Fall back to DuckDuckGo search

    # If restaurant URL doesn't work or doesn't contain menu info, search online
    return analyze_menu_by_name(name)

if __name__ == "__main__":
    restaurant_tab()
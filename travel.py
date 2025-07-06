import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from groq import Groq
import speech_recognition as sr
import pyttsx3
import threading
import time
import os
from dotenv import load_dotenv
import neo4j
from neo4j import GraphDatabase
import plotly.graph_objects as go
import plotly.express as px
import asyncio
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import base64

# Load environment variables
load_dotenv()

# Initialize APIs
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily_api_key = os.getenv("TAVILY_API_KEY")
rapidapi_key = os.getenv("RAPIDAPI_KEY")
locationiq_key = os.getenv("LOCATIONIQ_API_KEY")
exchange_rate_key = os.getenv("EXCHANGE_RATE_API_KEY")
spoonacular_key = os.getenv("SPOONACULAR_API_KEY")

# CORAL Protocol Configuration
CORAL_SERVER_URL = os.getenv("CORAL_SERVER_URL", "http://localhost:8000")
CORAL_PROTOCOL_ENABLED = os.getenv("CORAL_PROTOCOL_ENABLED", "true").lower() == "true"

# Neo4j Connection
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USERNAME")
neo4j_password = os.getenv("NEO4J_PASSWORD")

# Initialize voice engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.8)

# Modern UI Theme
def set_custom_theme():
    st.markdown(f"""
    <style>
        /* Main Theme */
        :root {{
            --primary: #6C63FF;
            --secondary: #FF6584;
            --accent: #36D1DC;
            --dark: #121826;
            --light: #F8F9FC;
            --card-bg: rgba(255, 255, 255, 0.95);
            --card-border: rgba(108, 99, 255, 0.2);
        }}
        
        [data-theme="dark"] {{
            --dark: #F8F9FC;
            --light: #121826;
            --card-bg: rgba(30, 30, 30, 0.95);
            --card-border: rgba(108, 99, 255, 0.4);
        }}
        
        .stApp {{
            background: linear-gradient(135deg, var(--light) 0%, #e6e9f0 100%);
            color: var(--dark);
        }}
        
        /* Cards */
        .unique-card {{
            background: var(--card-bg);
            border-radius: 20px;
            padding: 25px;
            margin: 15px 0;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
            border: 1px solid var(--card-border);
            backdrop-filter: blur(10px);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }}
        
        .unique-card:hover {{
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 15px 45px rgba(0, 0, 0, 0.2);
        }}
        
        /* Buttons */
        .stButton>button {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 14px 28px;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(108, 99, 255, 0.3);
        }}
        
        .stButton>button:hover {{
            transform: scale(1.05);
            box-shadow: 0 8px 25px rgba(108, 99, 255, 0.5);
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background: rgba(255, 255, 255, 0.7);
            border-radius: 12px 12px 0 0;
            padding: 14px 24px;
            transition: all 0.3s ease;
            font-weight: 600;
            margin: 0 5px;
        }}
        
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            box-shadow: 0 4px 15px rgba(108, 99, 255, 0.3);
        }}
        
        /* Voice Interface */
        .voice-interface {{
            background: linear-gradient(135deg, rgba(108, 99, 255, 0.1) 0%, rgba(54, 209, 220, 0.1) 100%);
            border-radius: 20px;
            padding: 30px;
            margin: 20px 0;
            text-align: center;
            border: 1px solid rgba(108, 99, 255, 0.15);
            backdrop-filter: blur(10px);
        }}
        
        /* Flight Card */
        .flight-card {{
            background: rgba(255, 255, 255, 0.9);
            border-radius: 16px;
            padding: 20px;
            margin: 15px 0;
            border-left: 5px solid var(--primary);
            transition: all 0.3s ease;
        }}
        
        .flight-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(108, 99, 255, 0.15);
        }}
        
        /* Animation */
        @keyframes float {{
            0% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
            100% {{ transform: translateY(0px); }}
        }}
        
        .floating {{
            animation: float 4s ease-in-out infinite;
        }}
        
        /* Coral Badge */
        .coral-badge {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: linear-gradient(135deg, #FF6584 0%, #6C63FF 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 30px;
            font-weight: bold;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
            z-index: 1000;
        }}
    </style>
    """, unsafe_allow_html=True)

set_custom_theme()

# Coral Protocol Integration
def coral_send_data(data_type: str, data: Dict):
    if not CORAL_PROTOCOL_ENABLED:
        return
    
    try:
        payload = {
            "type": data_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "VoyagerAI"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-CORAL-AUTH": os.getenv("CORAL_AUTH_TOKEN", "default_token")
        }
        
        response = requests.post(
            f"{CORAL_SERVER_URL}/ingest",
            data=json.dumps(payload),
            headers=headers,
            timeout=5
        )
        
        if response.status_code != 200:
            st.error(f"Coral error: {response.text}")
    except Exception as e:
        st.error(f"Coral connection failed: {str(e)}")

# Voice Assistant Functions
def speak(text):
    def speak_thread():
        engine.say(text)
        engine.runAndWait()
    
    thread = threading.Thread(target=speak_thread)
    thread.start()

def recognize_speech():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Speak now!")
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            coral_send_data("voice_input", {"text": text})
            return text
        except sr.UnknownValueError:
            return "Sorry, I didn't understand that."
        except sr.RequestError:
            return "Sorry, my speech service is down."

# Flight Search Functions
def search_flights(origin, destination, departure_date, passengers=1):
    """Search flights using Aerodatabox API via RapidAPI"""
    url = f"https://aerodatabox.p.rapidapi.com/flights/airports/iata/{origin}/{departure_date}T06:00/{departure_date}T20:00"
    
    querystring = {
        "withLeg": "true",
        "direction": "Departure",
        "withCancelled": "false",
        "withCodeshared": "true",
        "withCargo": "false",
        "withPrivate": "false"
    }
    
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            flights = response.json()
            # Filter flights going to our destination
            filtered_flights = [
                flight for flight in flights.get('departures', []) 
                if flight.get('arrival', {}).get('airport', {}).get('iata', '').upper() == destination.upper()
            ]
            return filtered_flights[:5]  # Return top 5 flights
        return []
    except Exception as e:
        st.error(f"Error fetching flights: {str(e)}")
        return []

def get_location_info(city):
    """Get location info using LocationIQ API"""
    url = f"https://us1.locationiq.com/v1/search.php"
    params = {
        "key": locationiq_key,
        "q": city,
        "format": "json",
        "limit": 1
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data:
                return {
                    "city": data[0].get("display_name", city),
                    "lat": float(data[0].get("lat", 0)),
                    "lon": float(data[0].get("lon", 0))
                }
    except Exception as e:
        st.error(f"Location error: {str(e)}")
    
    return {"city": city, "lat": 0, "lon": 0}

# Hotel Search Functions
def search_hotels(destination, checkin_date, checkout_date, guests=1):
    """Search hotels using Booking.com API via RapidAPI"""
    # First get location ID for destination
    location_info = get_location_info(destination)
    
    url = "https://booking-com.p.rapidapi.com/v1/hotels/search-by-coordinates"
    
    querystring = {
        "checkin_date": checkin_date,
        "checkout_date": checkout_date,
        "latitude": location_info["lat"],
        "longitude": location_info["lon"],
        "adults_number": str(guests),
        "order_by": "popularity",
        "filter_by_currency": "USD",
        "locale": "en-us",
        "room_number": "1"
    }
    
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            return response.json().get('result', [])[:5]  # Return top 5 hotels
        return []
    except Exception as e:
        st.error(f"Error fetching hotels: {str(e)}")
        return []

# Shopping Functions
def search_ebay_products(query):
    """Search products on eBay"""
    url = "https://ebay-search-result.p.rapidapi.com/search/" + query
    
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "ebay-search-result.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('results', [])[:5]  # Return top 5 results
        return []
    except Exception as e:
        st.error(f"Error searching eBay: {str(e)}")
        return []

def search_aliexpress_products(query):
    """Search products on AliExpress"""
    url = "https://aliexpress-datahub.p.rapidapi.com/item_search"
    
    querystring = {"q": query, "page": "1"}
    
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "aliexpress-datahub.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            return response.json().get('result', {}).get('resultList', [])[:5]  # Return top 5 results
        return []
    except Exception as e:
        st.error(f"Error searching AliExpress: {str(e)}")
        return []

# Recipe Functions
def search_recipes(query):
    """Search recipes using Spoonacular API"""
    url = "https://api.spoonacular.com/recipes/complexSearch"
    
    params = {
        "apiKey": spoonacular_key,
        "query": query,
        "number": 5,
        "instructionsRequired": True
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('results', [])
        return []
    except Exception as e:
        st.error(f"Error searching recipes: {str(e)}")
        return []

def get_recipe_details(recipe_id):
    """Get detailed recipe information"""
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    
    params = {
        "apiKey": spoonacular_key,
        "includeNutrition": False
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching recipe details: {str(e)}")
        return None

# Knowledge Graph Functions
def store_search_history(user_id, search_type, search_params):
    """Store search history in Neo4j"""
    if not neo4j_uri:
        return False
        
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        with driver.session() as session:
            query = """
            MERGE (u:User {id: $user_id})
            CREATE (s:Search {
                type: $search_type,
                params: $search_params,
                timestamp: datetime()
            })
            CREATE (u)-[:PERFORMED]->(s)
            """
            session.run(query, 
                user_id=user_id,
                search_type=search_type,
                search_params=json.dumps(search_params)
            )
            
        return True
        
    except Exception as e:
        st.error(f"Knowledge graph error: {str(e)}")
        return False

def get_search_history(user_id):
    """Get search history from Neo4j"""
    if not neo4j_uri:
        return []
        
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        with driver.session() as session:
            query = """
            MATCH (u:User {id: $user_id})-[:PERFORMED]->(s:Search)
            RETURN s.type AS type, s.params AS params, s.timestamp AS timestamp
            ORDER BY s.timestamp DESC
            LIMIT 10
            """
            result = session.run(query, user_id=user_id)
            return [dict(record) for record in result]
            
    except Exception as e:
        st.error(f"Knowledge graph error: {str(e)}")
        return []

# Currency Conversion
def convert_currency(amount, from_currency, to_currency):
    """Convert currency using ExchangeRate-API"""
    url = f"https://v6.exchangerate-api.com/v6/{exchange_rate_key}/pair/{from_currency}/{to_currency}/{amount}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get('conversion_result', amount)
        return amount
    except Exception as e:
        st.error(f"Currency conversion error: {str(e)}")
        return amount

# Recommendation System
def generate_recommendations(user_id):
    """Generate personalized recommendations based on search history"""
    history = get_search_history(user_id)
    if not history:
        return []
    
    # Extract interests from search history
    interests = set()
    for item in history:
        if item['type'] == 'flight_search':
            interests.add(item['params']['destination'])
        elif item['type'] == 'hotel_search':
            interests.add(item['params']['destination'])
        elif item['type'] == 'recipe_search':
            interests.add(item['params']['query'])
        elif item['type'] == 'shopping_search':
            interests.add(item['params']['query'])
    
    # Generate recommendations using GROQ
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a travel recommendation assistant. Based on the user's interests, suggest 3 personalized travel recommendations."
                },
                {
                    "role": "user",
                    "content": f"User interests: {', '.join(interests)}. Please recommend 3 travel destinations or activities."
                }
            ],
            model="llama3-70b-8192",
            max_tokens=300
        )
        
        recommendations = response.choices[0].message.content.split("\n")
        return [rec for rec in recommendations if rec.strip() and len(rec) > 10][:3]
    
    except Exception as e:
        st.error(f"Recommendation error: {str(e)}")
        return []

# Main App
def main():
    # Coral badge
    if CORAL_PROTOCOL_ENABLED:
        st.markdown('<div class="coral-badge">CORAL Protocol Active</div>', unsafe_allow_html=True)
    
    # Header with animation
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/2065/2065067.png", width=100, output_format="PNG")
    with col2:
        st.title("🌍 Voyager AI Travel Assistant")
        st.markdown("Your intelligent travel companion with voice interaction")
    
    # Initialize session state
    if 'voice_input' not in st.session_state:
        st.session_state.voice_input = ""
    if 'flights' not in st.session_state:
        st.session_state.flights = []
    if 'hotels' not in st.session_state:
        st.session_state.hotels = []
    if 'recipes' not in st.session_state:
        st.session_state.recipes = []
    if 'products' not in st.session_state:
        st.session_state.products = []
    if 'conversation' not in st.session_state:
        st.session_state.conversation = []
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = []
    
    # User ID for knowledge graph
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "user_" + str(uuid.uuid4())[:8]
    
    # Voice Interface
    st.markdown("""
    <div class="voice-interface">
        <h3>🎤 Voice Assistant</h3>
        <p>Ask me anything about travel, shopping, or recipes</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎤 Speak to Assistant", key="speak_button"):
            st.session_state.voice_input = recognize_speech()
            st.experimental_rerun()
    
    with col2:
        if st.button("🔊 Hear Response", key="hear_button"):
            if st.session_state.conversation:
                last_response = st.session_state.conversation[-1]['response']
                speak(last_response)
            else:
                speak("I don't have anything to say yet. Please ask me something first.")
    
    if st.session_state.voice_input:
        st.markdown(f"""
        <div class="unique-card">
            <h4>You said:</h4>
            <p>{st.session_state.voice_input}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Process voice input with Groq
        try:
            response = groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful travel assistant. Analyze the user's request and determine the intent. 
                        Respond with a JSON object containing: 
                        - intent (flight_search, hotel_search, shopping, recipe, general_question)
                        - parameters (extracted from the request)
                        - response (your natural language response)
                        """
                    },
                    {
                        "role": "user",
                        "content": st.session_state.voice_input
                    }
                ],
                model="llama3-8b-8192",
                response_format={"type": "json_object"}
            )

            parsed_response = json.loads(response.choices[0].message.content)
            intent = parsed_response.get('intent', 'general_question')
            parameters = parsed_response.get('parameters', {})
            ai_response = parsed_response.get('response', "I'll help with that.")

            # Store conversation
            st.session_state.conversation.append({
                'user': st.session_state.voice_input,
                'response': ai_response,
                'intent': intent,
                'timestamp': datetime.now().isoformat()
            })

            # Display response
            st.markdown(f"""
            <div class="unique-card">
                <h4>Assistant:</h4>
                <p>{ai_response}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Send to Coral
            coral_send_data("voice_interaction", {
                "input": st.session_state.voice_input,
                "intent": intent,
                "response": ai_response
            })
        except Exception as e:
            st.error(f"Error processing voice input: {str(e)}")
            intent = None
            parameters = {}
            ai_response = ""
        
        # Handle specific intents
        if intent == "flight_search":
            origin = parameters.get('origin', 'New York')
            destination = parameters.get('destination', 'London')
            date = parameters.get('date', (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))
            passengers = parameters.get('passengers', 1)

            with st.spinner("Searching for flights..."):
                try:
                    flights = search_flights(origin, destination, date, passengers)
                    st.session_state.flights = flights
                    
                    if flights:
                        st.success(f"Found {len(flights)} flights from {origin} to {destination}")

                        # Show flight map
                        origin_info = get_location_info(origin)
                        dest_info = get_location_info(destination)

                        fig = go.Figure()

                        # Add route line
                        fig.add_trace(go.Scattermapbox(
                            mode="lines",
                            lon=[origin_info["lon"], dest_info["lon"]],
                            lat=[origin_info["lat"], dest_info["lat"]],
                            line=dict(width=3, color="#6C63FF"),
                            name="Flight Route"
                        ))

                        # Add origin and destination markers
                        fig.add_trace(go.Scattermapbox(
                            mode="markers",
                            lon=[origin_info["lon"], dest_info["lon"]],
                            lat=[origin_info["lat"], dest_info["lat"]],
                            marker=dict(size=15, color=["#FF6584", "#6C63FF"]),
                            text=[f"🛫 {origin}", f"🛬 {destination}"],
                            name="Airports"
                        ))

                        fig.update_layout(
                            mapbox=dict(
                                style="carto-positron",
                                zoom=3,
                                center=dict(
                                    lat=(origin_info["lat"] + dest_info["lat"]) / 2,
                                    lon=(origin_info["lon"] + dest_info["lon"]) / 2
                                )
                            ),
                            height=400,
                            margin=dict(l=0, r=0, t=0, b=0),
                            title=f"Flight Route: {origin} to {destination}"
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        # Display flights
                        for flight in flights:
                            airline = flight.get('airline', {}).get('name', 'Unknown Airline')
                            flight_number = flight.get('number', 'N/A')
                            departure = flight.get('departure', {}).get('scheduledTime', {}).get('local', 'N/A')
                            arrival = flight.get('arrival', {}).get('scheduledTime', {}).get('local', 'N/A')

                            st.markdown(f"""
                            <div class="flight-card">
                                <h4>{airline} - Flight {flight_number}</h4>
                                <p>🛫 {departure} → 🛬 {arrival}</p>
                                <p>📍 From: {origin} → To: {destination}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.warning("No flights found for your criteria")

                    # Store in knowledge graph
                    store_search_history(st.session_state.user_id, "flight_search", {
                        "origin": origin,
                        "destination": destination,
                        "date": date,
                        "passengers": passengers
                    })
                except Exception as e:
                    st.error(f"Error processing request: {str(e)}")
            
        elif intent == "hotel_search":
            destination = parameters.get('destination', 'Paris')
            checkin = parameters.get('checkin', (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))
            checkout = parameters.get('checkout', (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'))
            guests = parameters.get('guests', 2)
            
            with st.spinner("Searching for hotels..."):
                try:
                    hotels = search_hotels(destination, checkin, checkout, guests)
                    st.session_state.hotels = hotels
                    
                    if hotels:
                        st.success(f"Found {len(hotels)} hotels in {destination}")
                        
                        # Show hotels on map
                        hotel_locations = []
                        for hotel in hotels:
                            if 'latitude' in hotel and 'longitude' in hotel:
                                hotel_locations.append({
                                    "name": hotel.get('hotel_name', 'Unknown Hotel'),
                                    "lat": hotel['latitude'],
                                    "lon": hotel['longitude'],
                                    "price": hotel.get('min_total_price', 'N/A')
                                })
                        
                        if hotel_locations:
                            df = pd.DataFrame(hotel_locations)
                            fig = px.scatter_mapbox(df, lat="lat", lon="lon", 
                                                    hover_name="name", hover_data=["price"],
                                                    color_discrete_sequence=["#6C63FF"],
                                                    zoom=12)
                            fig.update_layout(mapbox_style="carto-positron")
                            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Display hotels
                        for hotel in hotels:
                            st.markdown(f"""
                            <div class="unique-card">
                                <h4>{hotel.get('hotel_name', 'Unknown Hotel')}</h4>
                                <p>⭐ {hotel.get('review_score', 'N/A')} ({hotel.get('review_count', 'N/A')} reviews)</p>
                                <p>💰 ${hotel.get('min_total_price', 'N/A')} total for stay</p>
                                <p>📍 {hotel.get('address', 'N/A')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.warning("No hotels found for your criteria")
                        
                    # Store in knowledge graph
                    store_search_history(st.session_state.user_id, "hotel_search", {
                        "destination": destination,
                        "checkin": checkin,
                        "checkout": checkout,
                        "guests": guests
                    })
                except Exception as e:
                    st.error(f"Error processing request: {str(e)}")
        
        elif intent == "shopping":
            query = parameters.get('query', 'electronics')
            
            with st.spinner("Searching for products..."):
                try:
                    ebay_results = search_ebay_products(query)
                    aliexpress_results = search_aliexpress_products(query)
                    
                    st.session_state.products = {
                        'ebay': ebay_results,
                        'aliexpress': aliexpress_results
                    }
                    
                    if ebay_results or aliexpress_results:
                        st.success(f"Found shopping results for '{query}'")
                        
                        # Display eBay results
                        if ebay_results:
                            st.subheader("eBay Results")
                            for product in ebay_results:
                                st.markdown(f"""
                                <div class="unique-card">
                                    <h4>{product.get('title', 'No title')}</h4>
                                    <p>💰 ${product.get('price', {}).get('value', 'N/A')}</p>
                                    <p>🚚 {product.get('shipping', {}).get('cost', {}).get('value', 'N/A')}</p>
                                    <a href="{product.get('itemUrl', '#')}" target="_blank">View on eBay</a>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Display AliExpress results
                        if aliexpress_results:
                            st.subheader("AliExpress Results")
                            for product in aliexpress_results:
                                st.markdown(f"""
                                <div class="unique-card">
                                    <h4>{product.get('title', 'No title')}</h4>
                                    <p>💰 ${product.get('price', {}).get('value', 'N/A')}</p>
                                    <p>⭐ {product.get('rating', 'N/A')} ({product.get('orders', 'N/A')} orders)</p>
                                    <a href="{product.get('itemUrl', '#')}" target="_blank">View on AliExpress</a>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.warning("No products found for your search")
                        
                    # Store in knowledge graph
                    store_search_history(st.session_state.user_id, "shopping_search", {
                        "query": query
                    })
                except Exception as e:
                    st.error(f"Error processing request: {str(e)}")
        
        elif intent == "recipe":
            query = parameters.get('query', 'pasta')
            
            with st.spinner("Searching for recipes..."):
                try:
                    recipes = search_recipes(query)
                    st.session_state.recipes = recipes
                    
                    if recipes:
                        st.success(f"Found {len(recipes)} recipes for '{query}'")
                        
                        for recipe in recipes:
                            st.markdown(f"""
                            <div class="unique-card">
                                <h4>{recipe.get('title', 'No title')}</h4>
                                <p>⏱️ Ready in {recipe.get('readyInMinutes', 'N/A')} minutes</p>
                                <p>👨‍🍳 {recipe.get('servings', 'N/A')} servings</p>
                                <img src="{recipe.get('image', '')}" width="100%">
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.warning("No recipes found for your search")
                        
                    # Store in knowledge graph
                    store_search_history(st.session_state.user_id, "recipe_search", {
                        "query": query
                    })
                except Exception as e:
                    st.error(f"Error processing request: {str(e)}")
        
        # Clear voice input
        st.session_state.voice_input = ""
    
    # Recommendations Section
    if st.button("✨ Get Personalized Recommendations"):
        with st.spinner("Generating recommendations based on your history..."):
            st.session_state.recommendations = generate_recommendations(st.session_state.user_id)
    
    if st.session_state.recommendations:
        st.markdown("""
        <div class="unique-card">
            <h3>🌟 Personalized Recommendations</h3>
            <p>Based on your search history</p>
        </div>
        """, unsafe_allow_html=True)
        
        for rec in st.session_state.recommendations:
            st.markdown(f"""
            <div class="unique-card">
                <h4>✨ {rec}</h4>
            </div>
            """, unsafe_allow_html=True)
    
    # Manual Search Options
    st.markdown("""
    <div class="unique-card">
        <h3>🔍 Manual Search Options</h3>
        <p>Prefer typing? Use these search options</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Flights ✈️", "Hotels 🏨", "Shopping 🛒", "Recipes 🍳"])
    
    with tab1:
        st.subheader("Flight Search")
        col1, col2 = st.columns(2)
        
        with col1:
            manual_origin = st.text_input("From", "New York")
            manual_departure = st.date_input("Departure", datetime.now() + timedelta(days=7))
        
        with col2:
            manual_destination = st.text_input("To", "London")
            manual_passengers = st.number_input("Passengers", 1, 10, 1)
        
        if st.button("Search Flights", key="manual_flight_search"):
            with st.spinner("Searching flights..."):
                flights = search_flights(manual_origin, manual_destination, manual_departure.strftime('%Y-%m-%d'), manual_passengers)
                st.session_state.flights = flights
                
                if flights:
                    st.success(f"Found {len(flights)} flights")
                    # Store in knowledge graph
                    store_search_history(st.session_state.user_id, "flight_search", {
                        "origin": manual_origin,
                        "destination": manual_destination,
                        "date": manual_departure.strftime('%Y-%m-%d'),
                        "passengers": manual_passengers
                    })
                else:
                    st.warning("No flights found")
    
    with tab2:
        st.subheader("Hotel Search")
        col1, col2 = st.columns(2)
        
        with col1:
            hotel_destination = st.text_input("Destination", "Paris")
            hotel_checkin = st.date_input("Check-in", datetime.now() + timedelta(days=7))
        
        with col2:
            hotel_guests = st.number_input("Guests", 1, 10, 2)
            hotel_checkout = st.date_input("Check-out", datetime.now() + timedelta(days=14))
        
        if st.button("Search Hotels", key="manual_hotel_search"):
            with st.spinner("Searching hotels..."):
                hotels = search_hotels(hotel_destination, hotel_checkin.strftime('%Y-%m-%d'), hotel_checkout.strftime('%Y-%m-%d'), hotel_guests)
                st.session_state.hotels = hotels
                
                if hotels:
                    st.success(f"Found {len(hotels)} hotels")
                    # Store in knowledge graph
                    store_search_history(st.session_state.user_id, "hotel_search", {
                        "destination": hotel_destination,
                        "checkin": hotel_checkin.strftime('%Y-%m-%d'),
                        "checkout": hotel_checkout.strftime('%Y-%m-%d'),
                        "guests": hotel_guests
                    })
                else:
                    st.warning("No hotels found")
    
    with tab3:
        st.subheader("Product Search")
        product_query = st.text_input("What are you looking for?", "wireless headphones")
        platform = st.radio("Platform", ["eBay", "AliExpress", "Both"])
        
        if st.button("Search Products", key="manual_product_search"):
            with st.spinner("Searching products..."):
                ebay_results = []
                aliexpress_results = []
                
                if platform in ["eBay", "Both"]:
                    ebay_results = search_ebay_products(product_query)
                
                if platform in ["AliExpress", "Both"]:
                    aliexpress_results = search_aliexpress_products(product_query)
                
                st.session_state.products = {
                    'ebay': ebay_results,
                    'aliexpress': aliexpress_results
                }
                
                if ebay_results or aliexpress_results:
                    st.success(f"Found {len(ebay_results) + len(aliexpress_results)} products")
                    # Store in knowledge graph
                    store_search_history(st.session_state.user_id, "shopping_search", {
                        "query": product_query
                    })
                else:
                    st.warning("No products found")
    
    with tab4:
        st.subheader("Recipe Search")
        recipe_query = st.text_input("What would you like to cook?", "pasta")

        if st.button("Search Recipes", key="manual_recipe_search"):
            with st.spinner("Searching recipes..."):
                recipes = search_recipes(recipe_query)
                st.session_state.recipes = recipes

                if recipes:
                    st.success(f"Found {len(recipes)} recipes")
                    # Store in knowledge graph
                    store_search_history(st.session_state.user_id, "recipe_search", {
                        "query": recipe_query
                    })
                else:
                    st.warning("No recipes found")

        st.markdown("---")
        st.subheader("Restaurant Search")
        restaurant_query = st.text_input("Find restaurants in (city or location)", "New York")
        cuisine_query = st.text_input("Cuisine (optional)", "")

        def search_restaurants(location, cuisine=""):
            """Search restaurants using Yelp Fusion API via RapidAPI"""
            url = "https://yelp-com.p.rapidapi.com/businesses/search"
            querystring = {
                "location": location,
                "term": cuisine if cuisine else "restaurant",
                "limit": "5",
                "sort_by": "rating"
            }
            headers = {
                "X-RapidAPI-Key": rapidapi_key,
                "X-RapidAPI-Host": "yelp-com.p.rapidapi.com"
            }
            try:
                response = requests.get(url, headers=headers, params=querystring)
                if response.status_code == 200:
                    return response.json().get('businesses', [])
                return []
            except Exception as e:
                st.error(f"Error searching restaurants: {str(e)}")
                return []

        def get_restaurant_menu(restaurant_id):
            """Get restaurant menu using Yelp Fusion API via RapidAPI (if available)"""
            url = f"https://yelp-com.p.rapidapi.com/businesses/{restaurant_id}/menu"
            headers = {
                "X-RapidAPI-Key": rapidapi_key,
                "X-RapidAPI-Host": "yelp-com.p.rapidapi.com"
            }
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    return response.json().get('menu', [])
                return []
            except Exception as e:
                st.error(f"Error fetching menu: {str(e)}")
                return []

        if st.button("Search Restaurants", key="manual_restaurant_search"):
            with st.spinner("Searching restaurants..."):
                restaurants = search_restaurants(restaurant_query, cuisine_query)
                if restaurants:
                    st.success(f"Found {len(restaurants)} restaurants")
                    for rest in restaurants:
                        st.markdown(f"""
                        <div class="unique-card">
                            <h4>{rest.get('name', 'Unknown')}</h4>
                            <p>⭐ {rest.get('rating', 'N/A')} ({rest.get('review_count', 'N/A')} reviews)</p>
                            <p>📍 {', '.join(rest.get('location', {}).get('display_address', []))}</p>
                            <p>🍽️ {', '.join(rest.get('categories', [{}])[0].get('title', '') for c in rest.get('categories', []))}</p>
                            <a href="{rest.get('url', '#')}" target="_blank">View on Yelp</a>
                        </div>
                        """, unsafe_allow_html=True)
                        # Menu lookup
                        if st.button(f"Show Menu for {rest.get('name', '')}", key=f"menu_{rest.get('id', '')}"):
                            menu = get_restaurant_menu(rest.get('id', ''))
                            if menu:
                                st.markdown(f"<div class='unique-card'><h5>Menu for {rest.get('name', '')}</h5>", unsafe_allow_html=True)
                                for section in menu:
                                    st.markdown(f"**{section.get('name', '')}**")
                                    for item in section.get('items', []):
                                        st.markdown(f"- {item.get('name', '')}: {item.get('price', '')} - {item.get('description', '')}")
                                st.markdown("</div>", unsafe_allow_html=True)
                            else:
                                st.info("Menu not available for this restaurant.")
                else:
                    st.warning("No restaurants found")
    
    # Conversation History
    if st.session_state.conversation:
        st.markdown("""
        <div class="unique-card">
            <h3>💬 Conversation History</h3>
            <p>Your recent interactions with the assistant</p>
        </div>
        """, unsafe_allow_html=True)
        for chat in reversed(st.session_state.conversation):
            st.markdown(f"""
            <div class="unique-card">
                <p><strong>You:</strong> {chat['user']}</p>
                <p><strong>Assistant:</strong> {chat['response']}</p>
                <p style="font-size: 0.8em; color: #666;">{datetime.fromisoformat(chat['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
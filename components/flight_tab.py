# Flight search functionality


import streamlit as st
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go
from neo4j import GraphDatabase
from config import RAPIDAPI_KEY, LOCATIONIQ_API_KEY, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

def store_flight_search(user_id, origin, destination, date, passengers):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            session.run("""
            MERGE (u:User {id: $user_id})
            MERGE (o:Airport {code: $origin})
            MERGE (d:Airport {code: $destination})
            CREATE (s:Search {
                type: 'flight',
                date: $date,
                passengers: $passengers,
                timestamp: datetime()
            })
            CREATE (u)-[:SEARCHED]->(s)
            CREATE (s)-[:FROM]->(o)
            CREATE (s)-[:TO]->(d)
            """, 
            user_id=user_id, origin=origin, destination=destination, 
            date=date, passengers=passengers)
    except Exception as e:
        st.error(f"Failed to save search: {str(e)}")
    finally:
        driver.close()

def flight_tab(voice_input=None):
    st.header("✈️ Flight Search")
    
    # Voice input handling
    if voice_input:
        st.info(f"Voice input received: {voice_input}")
    
    # Search form
    col1, col2 = st.columns(2)
    with col1:
        origin = st.text_input("From (IATA code)", "JFK")
        departure = st.date_input("Departure", datetime.now() + timedelta(days=7))
    with col2:
        destination = st.text_input("To (IATA code)", "LHR")
        passengers = st.number_input("Passengers", 1, 10, 1)
    
    if st.button("Search Flights"):
        with st.spinner("Searching flights..."):
            flights = search_flights(origin, destination, departure.strftime('%Y-%m-%d'))
            if flights:
                store_flight_search(st.session_state.user_id, origin, destination, 
                                  departure.strftime('%Y-%m-%d'), passengers)
                display_flights(flights, origin, destination)
            else:
                st.warning("No flights found")

def search_flights(origin, destination, date):
    url = f"https://aerodatabox.p.rapidapi.com/flights/airports/iata/{origin}/{date}T06:00/{date}T20:00"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
    }
    params = {"withLeg": "true", "direction": "Departure"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            flights = response.json().get('departures', [])
            return [f for f in flights 
                   if f.get('arrival', {}).get('airport', {}).get('iata', '').upper() == destination.upper()][:5]
    except Exception as e:
        st.error(f"Error: {str(e)}")
    return []

def display_flights(flights, origin, destination):
    # Show flight map (implementation remains the same)
    # Display flight cards
    for flight in flights:
        airline = flight.get('airline', {}).get('name', 'Unknown')
        flight_number = flight.get('number', 'N/A')
        depart_time = flight.get('departure', {}).get('scheduledTime', {}).get('local', 'N/A')
        arrive_time = flight.get('arrival', {}).get('scheduledTime', {}).get('local', 'N/A')
        
        st.markdown(f"""
        <div class='modern-card'>
            <h4>{airline} Flight {flight_number}</h4>
            <p>🛫 {depart_time} → 🛬 {arrive_time}</p>
            <p>📍 {origin} → {destination}</p>
        </div>
        """, unsafe_allow_html=True)
# Flight search functionality
# Flight search functionality
import streamlit as st
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go
from components.ui_utils import modern_card
from config import RAPIDAPI_KEY, LOCATIONIQ_API_KEY, THEME

def flight_tab(voice_input=None):
    st.header("✈️ Flight Search")

    if voice_input:
        modern_card("Voice Input", f"You said: {voice_input}", "🎤")

    col1, col2 = st.columns(2)
    with col1:
        origin_city = st.text_input("From", "Dubai")
        departure = st.date_input("Departure", datetime.now() + timedelta(days=7))
    with col2:
        destination_city = st.text_input("To", "London")
        passengers = st.number_input("Passengers", 1, 10, 1)

    if st.button("Search Flights", key="flight_search"):
        with st.spinner("Finding flights..."):
            origin_iata = resolve_iata_code(origin_city)
            dest_iata = resolve_iata_code(destination_city)

            if not origin_iata or not dest_iata:
                st.error("Could not resolve IATA codes for the entered cities.")
                return

            flights = search_flights(origin_iata, dest_iata, departure.strftime('%Y-%m-%d'), passengers)
            st.session_state.flights = flights

            if flights:
                st.success(f"Found {len(flights)} flights")
                display_flights(flights, origin_city, destination_city)
            else:
                st.warning("No flights found or authentication failed")

def resolve_iata_code(city):
    url = "https://us1.locationiq.com/v1/search.php"
    params = {
        "key": LOCATIONIQ_API_KEY,
        "q": city,
        "format": "json",
        "limit": 1
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = data[0].get("lat")
                lon = data[0].get("lon")
                if lat and lon:
                    return get_nearest_airport_iata(lat, lon)
    except Exception as e:
        st.error(f"City-to-IATA error: {str(e)}")
    return None

def get_nearest_airport_iata(lat, lon):
    url = f"https://aerodatabox.p.rapidapi.com/airports/nearest/to/{lat}/{lon}/km/50/1"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("items", [{}])[0].get("iata")
        elif response.status_code == 401:
            st.error("Unauthorized: Check your RapidAPI key for Aerodatabox.")
    except Exception as e:
        st.error(f"Airport lookup failed: {str(e)}")
    return None

def search_flights(origin, destination, date, passengers=1):
    url = f"https://aerodatabox.p.rapidapi.com/flights/airports/iata/{origin}/{date}T06:00/{date}T20:00"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
    }
    params = {
        "withLeg": "true",
        "direction": "Departure",
        "withCancelled": "false"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            flights = response.json()
            return [f for f in flights.get('departures', []) 
                    if f.get('arrival', {}).get('airport', {}).get('iata', '').upper() == destination.upper()][:5]
        elif response.status_code == 401:
            st.error("Unauthorized: Check your RapidAPI key or subscription tier for Aerodatabox.")
        else:
            st.error(f"API returned status {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
    return []

def display_flights(flights, origin, destination):
    origin_info = get_location_info(origin)
    dest_info = get_location_info(destination)

    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        mode="lines",
        lon=[origin_info["lon"], dest_info["lon"]],
        lat=[origin_info["lat"], dest_info["lat"]],
        line=dict(width=3, color=THEME['primary']),
        name="Flight Route"
    ))
    fig.add_trace(go.Scattermapbox(
        mode="markers",
        lon=[origin_info["lon"], dest_info["lon"]],
        lat=[origin_info["lat"], dest_info["lat"]],
        marker=dict(size=15, color=[THEME['secondary'], THEME['primary']]),
        text=[f"🛫 {origin}", f"🛬 {destination}"],
        name="Airports"
    ))
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=3,
        mapbox_center={"lat": (origin_info["lat"] + dest_info["lat"])/2,
                       "lon": (origin_info["lon"] + dest_info["lon"])/2},
        height=400,
        margin={"l": 0, "r": 0, "t": 0, "b": 0}
    )
    st.plotly_chart(fig, use_container_width=True)

    for flight in flights:
        airline = flight.get('airline', {}).get('name', 'Unknown')
        number = flight.get('number', 'N/A')
        depart_time = flight.get('departure', {}).get('scheduledTime', {}).get('local', 'N/A')
        arrive_time = flight.get('arrival', {}).get('scheduledTime', {}).get('local', 'N/A')

        modern_card(
            f"{airline} Flight {number}",
            f"""
            🛫 **Departure:** {depart_time}  
            🛬 **Arrival:** {arrive_time}  
            📍 **Route:** {origin} → {destination}
            """,
            "✈️"
        )

def get_location_info(city):
    url = "https://us1.locationiq.com/v1/search.php"
    params = {
        "key": LOCATIONIQ_API_KEY,
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
        else:
            st.error(f"LocationIQ error {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"Location error: {str(e)}")
    return {"city": city, "lat": 0, "lon": 0}

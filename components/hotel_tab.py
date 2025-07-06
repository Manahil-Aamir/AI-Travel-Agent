# Hotel search functionality
import streamlit as st
import requests
from datetime import datetime, timedelta
import plotly.express as px
import pandas as pd
from components.ui_utils import modern_card
from config import RAPIDAPI_KEY, LOCATIONIQ_API_KEY, THEME

def hotel_tab(voice_input=None):
    st.header("🏨 Hotel Search")
    
    if voice_input:
        modern_card("Voice Input", f"You said: {voice_input}", "🎤")
    
    col1, col2 = st.columns(2)
    with col1:
        destination = st.text_input("Destination", "San Francisco")
        checkin = st.date_input("Check-in", datetime.now() + timedelta(days=7))
    with col2:
        guests = st.number_input("Guests", 1, 10, 2)
        checkout = st.date_input("Check-out", datetime.now() + timedelta(days=14))
    
    if st.button("Search Hotels", key="hotel_search"):
        with st.spinner("Finding hotels..."):
            hotels = search_hotels(destination, checkin.strftime('%Y-%m-%d'), 
                                 checkout.strftime('%Y-%m-%d'), guests)
            st.session_state.hotels = hotels
            
            if hotels:
                st.success(f"Found {len(hotels)} hotels")
                display_hotels(hotels, destination)
            else:
                st.warning("No hotels found")

def search_hotels(destination, checkin, checkout, guests=1):
    # First get location coordinates
    location = get_location_info(destination)
    
    url = "https://booking-com.p.rapidapi.com/v1/hotels/search-by-coordinates"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
    }
    params = {
        "checkin_date": checkin,
        "checkout_date": checkout,
        "latitude": location["lat"],
        "longitude": location["lon"],
        "adults_number": str(guests),
        "order_by": "popularity",
        "locale": "en-us"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get('result', [])[:5]
    except Exception as e:
        st.error(f"Error: {str(e)}")
    return []

def display_hotels(hotels, destination):
    # Show hotels on map
    hotel_locations = []
    for hotel in hotels:
        if 'latitude' in hotel and 'longitude' in hotel:
            hotel_locations.append({
                "name": hotel.get('hotel_name', 'Unknown'),
                "lat": hotel['latitude'],
                "lon": hotel['longitude'],
                "price": hotel.get('min_total_price', 'N/A')
            })
    
    if hotel_locations:
        df = pd.DataFrame(hotel_locations)
        fig = px.scatter_mapbox(df, lat="lat", lon="lon", hover_name="name",
                               hover_data=["price"], color_discrete_sequence=[THEME['primary']],
                               zoom=12)
        fig.update_layout(mapbox_style="carto-positron")
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
    
    # Display hotel cards
    for hotel in hotels:
        modern_card(
            hotel.get('hotel_name', 'Unknown Hotel'),
            f"""
            ⭐ **Rating:** {hotel.get('review_score', 'N/A')} ({hotel.get('review_count', 'N/A')} reviews)  
            💰 **Price:** ${hotel.get('min_total_price', 'N/A')} total  
            📍 **Address:** {hotel.get('address', 'N/A')}  
            🔗 **Book Now:** [View Deal](#)
            """,
            "🏨"
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
    except Exception:
        pass
    return {"city": city, "lat": 0, "lon": 0}
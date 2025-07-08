import streamlit as st
import requests
from datetime import datetime, timedelta
from neo4j import GraphDatabase
from config import RAPIDAPI_KEY, LOCATIONIQ_API_KEY, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
import re

# --- Airport lookup for Neo4j logging ---
def get_airport_iata(city):
    geo = requests.get(
        "https://us1.locationiq.com/v1/search.php",
        params={"key": LOCATIONIQ_API_KEY, "q": city, "format": "json", "limit": 1}
    )
    if geo.status_code != 200 or not geo.json():
        st.error(f"LocationIQ error for '{city}'")
        return None
    lat, lon = geo.json()[0]["lat"], geo.json()[0]["lon"]

    nearest = requests.get(
        f"https://aerodatabox.p.rapidapi.com/airports/search/location/{lat}/{lon}/km/100/16",
        headers={"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"}
    )
    if nearest.status_code != 200 or not nearest.json().get("items"):
        st.error(f"No airports found near '{city}'")
        return None

    for ap in nearest.json()["items"]:
        if ap.get("iata"):
            st.info(f"✈️ {city}: {ap['name']} ({ap['iata']})")
            return ap["iata"]
    return None

# --- Save search to Neo4j ---
def store_search(u, o, d, date, p):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    with driver.session() as s:
        s.run("""
          MERGE (u:User{id:$u})
          MERGE (o:Airport{code:$o})
          MERGE (d:Airport{code:$d})
          CREATE (s:Search{type:'flight',date:$date,passengers:$p,timestamp:datetime()})
          CREATE (u)-[:SEARCHED]->(s)
          CREATE (s)-[:FROM]->(o)
          CREATE (s)-[:TO]->(d)
        """, u=u, o=o, d=d, date=date, p=p)
    driver.close()

# --- Format for Kiwi API ---
def format_kiwi_location(name, country_code=None, is_country=False):
    slug = re.sub(r'\s+', '_', name.strip().lower())
    if is_country:
        return f"Country:{country_code.upper()}"
    return f"City:{slug}_{country_code.lower()}"

# --- Resolve input using LocationIQ + fallback to REST Countries API ---
def get_kiwi_location_format(place_name):
    url = "https://us1.locationiq.com/v1/search.php"
    params = {"key": LOCATIONIQ_API_KEY, "q": place_name, "format": "json", "limit": 1}
    try:
        r = requests.get(url, params=params)
        raw = r.json()
        st.write(f"📍 LocationIQ Response for '{place_name}':", raw)
        data = raw[0]

        address = data.get("address", {})
        country_code = address.get("country_code")

        if not country_code:
            display_name = data.get("display_name", "")
            country_name = display_name.split(",")[-1].strip()
            iso_lookup = requests.get(f"https://restcountries.com/v3.1/name/{country_name}")
            if iso_lookup.status_code == 200:
                iso_data = iso_lookup.json()
                country_code = iso_data[0]["cca2"].lower()

        country_code = country_code.upper() if country_code else "XX"

        city = (
            address.get("city") or address.get("town") or address.get("village") or
            data.get("display_name", "").split(",")[0].strip()
        )
        is_country = data.get("type") == "country"

        location = format_kiwi_location(city or place_name, country_code, is_country=is_country)
        st.write(f"✅ Formatted Kiwi Location for '{place_name}': {location}")
        return location
    except Exception as e:
        st.error(f"Location formatting failed for {place_name}: {e}")
        return None

# --- Call Kiwi API ---
def search_flights(origin_input, dest_input):
    source = get_kiwi_location_format(origin_input)
    dest = get_kiwi_location_format(dest_input)

    st.write("🔧 Kiwi API Params:")
    st.code(f"source = {source}\ndestination = {dest}", language="yaml")

    if not source or not dest:
        st.error("❌ Could not resolve city/country input.")
        return [], {}

    url = "https://kiwi-com-cheap-flights.p.rapidapi.com/round-trip"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "kiwi-com-cheap-flights.p.rapidapi.com"
    }
    params = {
        "source": source,
        "destination": dest,
        "currency": "usd",
        "locale": "en",
        "adults": 1,
        "children": 0,
        "infants": 0,
        "handbags": 1,
        "holdbags": 0,
        "cabinClass": "ECONOMY",
        "sortBy": "QUALITY",
        "sortOrder": "ASCENDING",
        "applyMixedClasses": "true",
        "allowReturnFromDifferentCity": "true",
        "allowChangeInboundDestination": "true",
        "allowChangeInboundSource": "true",
        "allowDifferentStationConnection": "true",
        "enableSelfTransfer": "true",
        "allowOvernightStopover": "true",
        "enableTrueHiddenCity": "true",
        "enableThrowAwayTicketing": "true",
        "outbound": "SUNDAY,MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY,SATURDAY",
        "transportTypes": "FLIGHT",
        "contentProviders": "FLIXBUS_DIRECTS,FRESH,KAYAK,KIWI",
        "limit": 5
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        st.write(f"📡 Kiwi API Response [{res.status_code}]: {res.text[:500]}...")

        if res.status_code == 200:
            data = res.json()
            return data.get("itineraries", []), data.get("metadata", {})
        else:
            st.error(f"Kiwi API error: {res.status_code}")
    except Exception as e:
        st.error(f"API failure: {e}")
    return [], {}

# --- Display Flights ---
def display_flights(itineraries, origin, dest, metadata=None):
    if not itineraries:
        st.warning("No flights found.")
        return

    st.subheader(f"🛫 {len(itineraries)} Itineraries from {origin} → {dest}")

    for i, itinerary in enumerate(itineraries, 1):
        try:
            price = itinerary.get("price", {}).get("amount", "N/A")
            outbound = itinerary.get("outbound", {}).get("sectorSegments", [])[0].get("segment", {})
            inbound = itinerary.get("inbound", {}).get("sectorSegments", [])[0].get("segment", {})

            dep_time = outbound.get("source", {}).get("localTime", "N/A")
            arr_time = outbound.get("destination", {}).get("localTime", "N/A")
            ret_time = inbound.get("source", {}).get("localTime", "N/A")
            ret_arr_time = inbound.get("destination", {}).get("localTime", "N/A")

            airline = outbound.get("carrier", {}).get("name", "Unknown Airline")

            st.markdown(f"""
            ### ✈️ Option {i}
            **Airline:** {airline}  
            🟢 **Depart:** {dep_time} → {arr_time}  
            🔁 **Return:** {ret_time} → {ret_arr_time}  
            💵 **Price:** {price} USD  
            ---
            """)

            for edge in itinerary.get("bookingOptions", {}).get("edges", []):
                node = edge.get("node", {})
                url = node.get("bookingUrl", "")
                full_url = f"https://www.kiwi.com{url}" if url else "N/A"
            st.markdown(f"[🔗 Book this flight]({full_url})")

        except Exception as e:
            st.warning(f"Could not render itinerary: {e}")

# --- Main Streamlit Tab ---
def flight_tab():
    st.header("✈️ Flight Search (Powered by Kiwi via RapidAPI)")

    ocity = st.text_input("From (city or country)", "Karachi")
    dcity = st.text_input("To (city or country)", "Dubai")
    date = st.date_input("Date", datetime.now() + timedelta(days=7))
    pax = st.number_input("Passengers", 1, 9, 1)

    if st.button("Search Flights"):
        oi = get_airport_iata(ocity)
        di = get_airport_iata(dcity)
        if oi and di:
            trips, metadata = search_flights(ocity, dcity)
            if "user_id" in st.session_state:
                store_search(st.session_state.user_id, oi, di, date.strftime("%Y-%m-%d"), pax)
            display_flights(trips, ocity, dcity, metadata)

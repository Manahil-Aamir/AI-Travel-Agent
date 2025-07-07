import streamlit as st
import requests
from datetime import datetime, timedelta
from neo4j import GraphDatabase
from config import RAPIDAPI_KEY, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

# Custom CSS for modern design
def load_css():
    st.markdown("""
    <style>
    .hotel-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .hotel-name {
        font-size: 1.2rem;
        font-weight: bold;
        color: #333;
    }
    .hotel-price {
        font-size: 1.5rem;
        color: #27ae60;
        font-weight: bold;
    }
    .hotel-rating {
        color: #e67e22;
        font-weight: 600;
    }
    .search-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def store_hotel_search(user_id, location, checkin, checkout, guests):
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run("""
            MERGE (u:User {id: $user_id})
            MERGE (c:City {name: $location})
            CREATE (s:Search {
                type: 'hotel',
                checkin: $checkin,
                checkout: $checkout,
                guests: $guests,
                timestamp: datetime()
            })
            CREATE (u)-[:SEARCHED]->(s)
            CREATE (s)-[:IN]->(c)
            """, 
            user_id=user_id, location=location, 
            checkin=checkin, checkout=checkout, guests=guests)
    except Exception as e:
        st.error(f"Failed to save search: {str(e)}")
    finally:
        driver.close()

def get_location_coordinates(destination):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": destination,
            "format": "json",
            "limit": 1
        }
        headers = {"User-Agent": "hotel-search-app"}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            return float(data["lat"]), float(data["lon"])
        return None, None
    except Exception as e:
        st.error(f"Geocoding error: {str(e)}")
        return None, None

def search_hotels(destination, checkin, checkout, guests):
    url = "https://booking-com18.p.rapidapi.com/stays/search-by-geo"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "booking-com18.p.rapidapi.com"
    }

    try:
        lat, lon = get_location_coordinates(destination)
        if not lat or not lon:
            st.error("Could not determine location coordinates")
            return []

        params = {
            "neLat": lat + 0.5,
            "neLng": lon + 0.5,
            "swLat": lat - 0.5,
            "swLng": lon - 0.5,
            "units": "metric",
            "checkinDate": checkin,
            "checkoutDate": checkout,
            "adults": str(guests),
            "order_by": "popularity",
            "currency": "USD"
        }

        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            hotels = []
            response_json = response.json()
            hotel_list = response_json.get("data", {}).get("results", [])
            for index, hotel_data in enumerate(hotel_list):
                try:
                    photo_urls = hotel_data['photoUrls'] if 'photoUrls' in hotel_data and isinstance(hotel_data['photoUrls'], list) else []
                    first_photo_url = photo_urls[0] if photo_urls else ''

                    price = hotel_data['priceBreakdown']['grossPrice']['amountRounded'] if 'priceBreakdown' in hotel_data and 'grossPrice' in hotel_data['priceBreakdown'] else 'N/A'
                    original_price = hotel_data['priceBreakdown']['strikethroughPrice']['amountRounded'] if 'strikethroughPrice' in hotel_data.get('priceBreakdown', {}) else ''
                    hotel = {
                        'id': hotel_data.get('basicPropertyData', {}).get('id'),
                        'name': hotel_data.get('basicPropertyData', {}).get('name', 'Unknown Hotel'),

                        'price': hotel_data.get('priceDisplayInfo', {}).get('displayPrice', {}).get('amountPerStay', {}).get('amountRounded', 'N/A'),
                        'original_price': hotel_data.get('priceDisplayInfo', {}).get('priceBeforeDiscount', {}).get('amountPerStay', {}).get('amountRounded', ''),

                        'review_score': hotel_data.get('basicPropertyData', {}).get('reviews', {}).get('totalScore', 0),
                        'review_count': hotel_data.get('basicPropertyData', {}).get('reviews', {}).get('reviewsCount', 0),
                        'review_word': hotel_data.get('basicPropertyData', {}).get('reviews', {}).get('totalScoreTextTag', {}).get('translation', 'No reviews'),

                        'photo_url': hotel_data.get('basicPropertyData', {}).get('photos', {}).get('main', {}).get('lowResJpegUrl', {}).get('absoluteUrl', ''),

                        'address': hotel_data.get('basicPropertyData', {}).get('location', {}).get('address', ''),
                        
                        'checkin_date': hotel_data.get('recommendedDate', {}).get('checkin', ''),
                        'checkout_date': hotel_data.get('recommendedDate', {}).get('checkout', ''),
                        
                        'checkin_time': hotel_data.get('checkinCheckoutPolicy', {}).get('checkinTimeFromFormatted', ''),
                        'checkout_time': hotel_data.get('checkinCheckoutPolicy', {}).get('checkoutTimeUntilFormatted', ''),
                        
                        'property_class': hotel_data.get('basicPropertyData', {}).get('starRating', {}).get('value', 0),
                        'longitude': hotel_data.get('basicPropertyData', {}).get('location', {}).get('longitude'),
                        'latitude': hotel_data.get('basicPropertyData', {}).get('location', {}).get('latitude'),
                    }
                    hotels.append(hotel)
                except Exception as e:
                    
                    print(f"Error processing hotel at index {index}: {str(e)}")
            return hotels[:15]  # Return first 15 hotels
        else:
            st.error(f"API Error: {response.status_code}")
            return []
            
    except Exception as e:
        #st.error(f"Search failed: {str(e)}")
        return []

def display_hotels(hotels):
    if not hotels:
        st.warning("No hotels found for your search criteria")
        return

    st.markdown(f"### 🏨 Found {len(hotels)} hotels")

    for hotel in hotels:
        hotel_id = str(hotel['id'])

        col1, col2 = st.columns([1, 2])

        with col1:
            if hotel['photo_url']:
                st.image(hotel['photo_url'], width=160)
            else:
                st.markdown("📸 No photo available")

        with col2:
            st.markdown(f"#### {hotel['name']}")
            st.markdown(f"⭐ **{hotel['review_score']}** — {hotel['review_word']} ({hotel['review_count']} reviews)")
            original_price = f"<span style='text-decoration:line-through; color:#888;'>{hotel['original_price']}</span>" if hotel['original_price'] else ''
            st.markdown(f"**💰 Price:** {hotel['price']} &nbsp; {original_price}", unsafe_allow_html=True)
            st.markdown(f"**🛎️ Stay Time:** {hotel['checkin_time']} - {hotel['checkout_time']}")
            st.markdown(f"**📍 Address:** {hotel['address']}")

            # Book Now Button
            book_key = f"book_{hotel_id}"
            if st.button("📦 Book Now", key=book_key):
                st.session_state[f"booked_{hotel_id}"] = True

            if st.session_state.get(f"booked_{hotel_id}", False):
                st.success(f"✅ {hotel['name']} has been booked!")

        st.markdown("---")


def show_hotel_details(hotel):
    with st.expander(f"🏨 Complete Details: {hotel['name']}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🏨 Hotel Information**")
            st.write(f"**Name:** {hotel['name']}")
            st.write(f"**ID:** {hotel['id']}")
            st.write(f"**Rating:** ⭐ {hotel['review_score']} ({hotel['review_word']})")
            st.write(f"**Reviews:** {hotel['review_count']}")
            st.write(f"**Class:** {hotel['property_class']}-star")
            
            st.markdown("**📍 Location**")
            st.write(f"**Address:** {hotel['address']}")

        with col2:
            st.markdown("**💰 Pricing**")
            st.write(f"**Current Price:** {hotel['price']}")
            if hotel['original_price']:
                st.write(f"**Original Price:** {hotel['original_price']}")

            st.markdown("**🕒 Check-in/out**")
            st.write(f"**Check-in:** {hotel.get('checkin_time', '?')}")
            st.write(f"**Check-out:** {hotel.get('checkout_time', '?')}")

        if hotel['photo_url']:
            st.markdown("**📸 Photo**")
            st.image(hotel['photo_url'], use_column_width=True)


def hotel_tab():
    load_css()
    st.markdown("""
    <div class="search-header">
        <h1>🏨 Hotel Search</h1>
        <p>Find your perfect stay</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("hotel_search_form"):
        col1, col2 = st.columns(2)
        with col1:
            destination = st.text_input("Destination", "Karachi")
            checkin = st.date_input("Check-in", datetime.now() + timedelta(days=7))
        with col2:
            guests = st.number_input("Guests", 1, 10, 2)
            checkout = st.date_input("Check-out", datetime.now() + timedelta(days=14))
        
        submitted = st.form_submit_button("Search Hotels")

    if submitted:
        if checkin >= checkout:
            st.error("Check-out date must be after check-in date")
            return

        with st.spinner("Searching hotels..."):
            hotels = search_hotels(destination, checkin.strftime('%Y-%m-%d'), 
                                 checkout.strftime('%Y-%m-%d'), guests)
            
            if hotels:
                if 'user_id' in st.session_state:
                    store_hotel_search(st.session_state.user_id, destination, 
                                     checkin.strftime('%Y-%m-%d'), 
                                     checkout.strftime('%Y-%m-%d'), guests)
                display_hotels(hotels)
            else:
                st.write("[DEBUG] No hotels returned from search_hotels")

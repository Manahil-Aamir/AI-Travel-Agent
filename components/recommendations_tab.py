from datetime import datetime
import streamlit as st
from neo4j import GraphDatabase
from components.ui_utils import modern_card
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, THEME

def recommendations_tab():
    st.header("✨ Personalized Recommendations")
    
    # Initialize Neo4j driver
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    # Get user ID from session state
    user_id = st.session_state.get('user_id', 'default_user')
    
    # Section 1: Recommended Destinations
    with st.spinner("Finding your perfect destinations..."):
        destinations = get_recommended_destinations(driver, user_id)
        if destinations:
            st.subheader("🌍 Recommended Destinations")
            cols = st.columns(min(3, len(destinations)))
            for idx, dest in enumerate(destinations[:3]):
                with cols[idx % 3]:
                    modern_card(
                        dest['name'],
                        f"""
                        ✈️ From {dest.get('origin', 'your location')}  
                        💰 Avg. price: ${dest.get('avg_price', 'N/A')}  
                        ⭐ Rating: {dest.get('rating', 'N/A')}/5  
                        🔗 [Explore](#)
                        """,
                        "📍"
                    )
    
    # Section 2: Recommended Hotels
    with st.spinner("Finding hotels you'll love..."):
        hotels = get_recommended_hotels(driver, user_id)
        if hotels:
            st.subheader("🏨 Recommended Hotels")
            for hotel in hotels[:3]:
                modern_card(
                    hotel['name'],
                    f"""
                    📍 {hotel.get('location', 'N/A')}  
                    💰 ${hotel.get('price', 'N/A')}/night  
                    ⭐ {hotel.get('rating', 'N/A')} ({hotel.get('reviews', 'N/A')} reviews)  
                    🛏️ {hotel.get('type', 'Hotel')}  
                    🔗 [View Deal](#)
                    """,
                    "🏨"
                )
    
    # Section 3: Travel Products
    with st.spinner("Finding travel gear for you..."):
        products = get_recommended_products(driver, user_id)
        if products:
            st.subheader("🛒 Recommended Travel Gear")
            cols = st.columns(min(3, len(products)))
            for idx, product in enumerate(products[:3]):
                with cols[idx % 3]:
                    modern_card(
                        product['name'],
                        f"""
                        💰 ${product.get('price', 'N/A')}  
                        ⭐ {product.get('rating', 'N/A')}/5  
                        🚚 {product.get('shipping', 'Free shipping')}  
                        🔗 [Buy Now](#)
                        """,
                        "🎒"
                    )
    
    driver.close()

def get_recommended_destinations(driver, user_id):
    query = """
    MATCH (u:User {id: $user_id})-[:SEARCHED]->(:Search)-[:FOR]->(d:Destination)
    WITH d, COUNT(*) AS searchCount
    MATCH (d)-[:HAS_WEATHER]->(w:Weather)
    WHERE w.season = $current_season
    OPTIONAL MATCH (d)-[:HAS_FLIGHT]->(f:Flight)
    WITH d, searchCount, AVG(f.price) AS avgPrice, COLLECT(DISTINCT f.origin)[0] AS origin
    RETURN d.name AS name, 
           origin,
           avgPrice AS avg_price,
           d.rating AS rating
    ORDER BY searchCount DESC, d.rating DESC
    LIMIT 5
    """
    
    seasons = ["winter", "spring", "summer", "fall"]
    current_month = datetime.now().month
    current_season = seasons[(current_month % 12) // 3]
    
    try:
        with driver.session() as session:
            result = session.run(query, user_id=user_id, current_season=current_season)
            return [dict(record) for record in result]
    except Exception as e:
        st.error(f"Error fetching destinations: {str(e)}")
        return []

def get_recommended_hotels(driver, user_id):
    query = """
    MATCH (u:User {id: $user_id})-[:SEARCHED]->(:Search {type: 'hotel'})-[:IN]->(c:City)
    MATCH (c)<-[:LOCATED_IN]-(h:Hotel)
    WHERE h.rating >= 4.0
    OPTIONAL MATCH (h)-[:HAS_AMENITY]->(a:Amenity)
    WITH h, c, COLLECT(DISTINCT a.name) AS amenities
    WHERE ANY(amenity IN ['Free WiFi', 'Pool', 'Breakfast'] WHERE amenity IN amenities)
    RETURN h.name AS name,
           c.name + ', ' + h.address AS location,
           h.price AS price,
           h.rating AS rating,
           h.reviewCount AS reviews,
           h.type AS type
    ORDER BY h.rating DESC
    LIMIT 5
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, user_id=user_id)
            return [dict(record) for record in result]
    except Exception as e:
        st.error(f"Error fetching hotels: {str(e)}")
        return []

def get_recommended_products(driver, user_id):
    query = """
    MATCH (u:User {id: $user_id})-[:SEARCHED]->(:Search {type: 'shopping'})-[:FOR]->(p:Product)
    WHERE p.category IN ['Luggage', 'Travel Gear', 'Electronics']
    OPTIONAL MATCH (p)-[:SIMILAR_TO]->(rec:Product)
    WHERE rec.rating >= 4.0 AND rec.price <= 200
    WITH COLLECT(DISTINCT p) + COLLECT(DISTINCT rec) AS products
    UNWIND products AS product
    RETURN DISTINCT product.name AS name,
           product.price AS price,
           product.rating AS rating,
           product.shipping AS shipping
    ORDER BY product.rating DESC
    LIMIT 6
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, user_id=user_id)
            return [dict(record) for record in result]
    except Exception as e:
        st.error(f"Error fetching products: {str(e)}")
        return []
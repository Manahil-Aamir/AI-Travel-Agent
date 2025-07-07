# Shopping functionality with voice interaction and fixed cart
import streamlit as st
# import streamlit.components.v1  # Not directly used, can be removed
import requests
import locale
import pycountry
from neo4j import GraphDatabase
from components.ui_utils import modern_card
from config import RAPIDAPI_KEY, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
# import json  # Not directly used, can be removed
import uuid
try:
    import speech_recognition as sr
    from gtts import gTTS
    VOICE_ENABLED = True
except ImportError:
    VOICE_ENABLED = False
    st.warning("Voice features disabled. Install speech_recognition and gtts: pip install SpeechRecognition gtts")
# import io  # Not directly used, can be removed
import base64
import tempfile
# import os  # Not directly used, can be removed

# Initialize session state for persistent data
def init_session_state():
    if "cart" not in st.session_state:
        st.session_state.cart = []
    if "checkout_stage" not in st.session_state:
        st.session_state.checkout_stage = None
    if "current_products" not in st.session_state:
        st.session_state.current_products = {'ebay': [], 'aliexpress': []}
    if "last_search_query" not in st.session_state:
        st.session_state.last_search_query = ""
    if "cart_updated" not in st.session_state:
        st.session_state.cart_updated = False
    if "voice_response" not in st.session_state:
        st.session_state.voice_response = ""
    if "audio_response" not in st.session_state:
        st.session_state.audio_response = None

# Initialize Neo4j driver
def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# Store search in Neo4j
def store_product_search(user_id, query, platform, results_count):
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run("""
            MERGE (u:User {id: $user_id})
            MERGE (p:ProductCategory {name: toLower($query)})
            CREATE (s:Search {
                type: 'shopping',
                query: $query,
                platform: $platform,
                results_count: $results_count,
                timestamp: datetime()
            })
            CREATE (u)-[:SEARCHED]->(s)
            CREATE (s)-[:FOR]->(p)
            FOREACH (ignore IN CASE WHEN $results_count > 0 THEN [1] ELSE [] END |
                MERGE (pop:PopularProduct {query: toLower($query)})
                SET pop.last_searched = datetime()
                SET pop.search_count = COALESCE(pop.search_count, 0) + 1
                MERGE (s)-[:RELATED_TO]->(pop)
            )
            """, 
            user_id=user_id, query=query, platform=platform, results_count=results_count)
    except Exception as e:
        st.error(f"Failed to save search: {str(e)}")
    finally:
        driver.close()

# Get recommended searches from Neo4j
def get_recommended_searches(user_id):
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("""
            MATCH (u:User {id: $user_id})-[:SEARCHED]->(s:Search)-[:FOR]->(p:ProductCategory)
            OPTIONAL MATCH (p)<-[:FOR]-(other:Search)-[:RELATED_TO]->(pop:PopularProduct)
            RETURN DISTINCT p.name AS query, 
                   COUNT(s) AS search_count,
                   COLLECT(DISTINCT pop.query)[..3] AS similar_searches
            ORDER BY search_count DESC
            LIMIT 5
            """, user_id=user_id)
            return [dict(record) for record in result]
    except Exception as e:
        st.error(f"Failed to get recommendations: {str(e)}")
        return []
    finally:
        driver.close()

# Detect user's country using locale
def detect_country():
    try:
        country_code = locale.getdefaultlocale()[0].split("_")[-1]
        if country_code:
            return country_code.upper()
    except:
        pass
    return "US"

# Search products function
def search_products(query, platform, country):
    products = {'ebay': [], 'aliexpress': []}

    if platform in ["eBay", "Both"]:
        try:
            url = f"https://ebay-search-result.p.rapidapi.com/search/{query}"
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": "ebay-search-result.p.rapidapi.com"
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                products['ebay'] = response.json().get('results', [])[:5]
        except Exception as e:
            st.error(f"eBay search error: {str(e)}")

    if platform in ["AliExpress", "Both"]:
        try:
            url = "https://aliexpress-business-api.p.rapidapi.com/textsearch.php"
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": "aliexpress-business-api.p.rapidapi.com"
            }
            params = {
                "keyWord": query,
                "pageSize": "20",
                "pageIndex": "1",
                "country": country,
                "currency": "USD",
                "lang": "en",
                "filter": "orders",
                "sortBy": "asc"
            }
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                products['aliexpress'] = response.json().get('result', {}).get('resultList', [])[:5]
        except Exception as e:
            st.error(f"AliExpress search error: {str(e)}")

    return products

# Voice input processing
def process_voice_input(text):
    """Process voice input and return appropriate response"""
    text_lower = text.lower()
    
    # Shopping commands
    if any(word in text_lower for word in ["buy", "shop", "search", "find"]):
        if "backpack" in text_lower:
            query = "travel backpack"
        elif "adapter" in text_lower or "charger" in text_lower:
            query = "travel power adapter"
        elif "suitcase" in text_lower or "luggage" in text_lower:
            query = "carry-on suitcase"
        elif "headphones" in text_lower:
            query = "travel headphones"
        elif "camera" in text_lower:
            query = "travel camera"
        else:
            # Extract product name from voice input
            query = text_lower.replace("buy", "").replace("shop for", "").replace("search for", "").replace("find", "").strip()
        
        st.session_state.shopping_query = query
        st.session_state.platform_select = "Both"
        return f"I'll search for {query} for you!"
    
    # Cart commands
    elif "cart" in text_lower:
        if "view" in text_lower or "show" in text_lower or "check" in text_lower:
            st.session_state.checkout_stage = "cart"
            return f"Here's your cart with {len(st.session_state.cart)} items"
        elif "clear" in text_lower or "empty" in text_lower:
            st.session_state.cart.clear()
            return "Your cart has been cleared"
    
    # Checkout commands
    elif "checkout" in text_lower or "order" in text_lower:
        if st.session_state.cart:
            st.session_state.checkout_stage = "checkout"
            return "Let's proceed to checkout"
        else:
            return "Your cart is empty. Add some items first!"
    
    else:
        return "I can help you search for products, manage your cart, or checkout. What would you like to do?"
    
# Add these functions to your shopping_tab.py file

def speech_to_text():
    """Convert speech to text using microphone input"""
    if not VOICE_ENABLED:
        return None
    
    try:
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Use microphone as source
        with sr.Microphone() as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # Listen for audio input
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            # Convert speech to text using Google's speech recognition
            text = recognizer.recognize_google(audio)
            return text
            
    except sr.UnknownValueError:
        st.error("Could not understand audio. Please try again.")
        return None
    except sr.RequestError as e:
        st.error(f"Could not request results from speech recognition service: {e}")
        return None
    except sr.WaitTimeoutError:
        st.error("Listening timeout. Please try again.")
        return None
    except Exception as e:
        st.error(f"Speech recognition error: {e}")
        return None

def text_to_speech(text):
    """Convert text to speech audio data"""
    if not VOICE_ENABLED:
        return None
    
    try:
        # Create gTTS object
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tts.save(tmp_file.name)
            
            # Read the audio file
            with open(tmp_file.name, 'rb') as audio_file:
                audio_data = audio_file.read()
        return audio_data
    except Exception as e:
        st.error(f"Text-to-speech error: {e}")
        return None

# Add to cart function with proper state management
def add_to_cart(product_data):
    """Add product to cart and update state"""
    # Generate unique ID for the cart item
    cart_item = {
        "id": str(uuid.uuid4()),
        "title": product_data["title"],
        "price": product_data["price"],
        "platform": product_data["platform"],
        "url": product_data["url"],
        "added_at": str(st.session_state.get("current_time", ""))
    }
    
    st.session_state.cart.append(cart_item)
    st.session_state.cart_updated = True
    st.session_state.voice_response = f"Added {product_data['title']} to your cart!"
def shopping_tab(voice_input=None):
    st.header("🛒 Travel Shopping Assistant")
    
    # Initialize session state
    init_session_state()

    # If voice_input is provided, process it as a voice command
    if voice_input and isinstance(voice_input, str) and voice_input.strip():
        response = process_voice_input(voice_input)
        st.session_state.voice_response = response
        # Optionally, generate audio for the response
        audio_data = text_to_speech(response)
        if audio_data:
            st.session_state.audio_response = audio_data
        st.session_state.auto_search = True

    # Voice input section with real speech recognition
    st.subheader("🎤 Voice Shopping Assistant")
    # Voice input section with real speech recognition
    st.subheader("🎤 Voice Shopping Assistant")
    
    # Voice input options
    voice_col1, voice_col2, voice_col3 = st.columns([2, 1, 1])
    
    with voice_col1:
        voice_text = st.text_input("Voice Input:", 
                                  placeholder="Type or use voice: 'Search for travel backpack', 'Show my cart', etc.")
    
    with voice_col2:
        if st.button("🎤 Start Listening", key="start_voice", disabled=not VOICE_ENABLED):
            if VOICE_ENABLED:
                st.session_state.listening = True
                with st.spinner("Listening... Please speak now!"):
                    recognized_text = speech_to_text()
                    if recognized_text:
                        st.session_state.voice_text = recognized_text
                        voice_text = recognized_text
                        st.rerun()
            else:
                st.error("Voice recognition not available. Please install required packages.")
    
    with voice_col3:
        if st.button("💬 Process Voice", key="process_voice"):
            if voice_text.strip():
                response = process_voice_input(voice_text)
                st.session_state.voice_response = response
                st.rerun()
    
    # Display voice response with audio playback
    if st.session_state.voice_response:
        st.success(f"🗣️ Assistant: {st.session_state.voice_response}")
        
        # Play audio response if available
        if st.session_state.audio_response:
            try:
                # Convert audio data to base64 for HTML audio player
                audio_base64 = base64.b64encode(st.session_state.audio_response).decode()
                audio_html = f"""
                <audio controls autoplay>
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>
                """
                st.components.v1.html(audio_html, height=60)
            except Exception as e:
                st.error(f"Audio playback error: {str(e)}")
        
        # Auto-execute search if triggered by voice
        if hasattr(st.session_state, 'auto_search') and st.session_state.auto_search:
            st.session_state.auto_search = False
            if st.session_state.shopping_query:
                # Auto-trigger search
                st.rerun()
    
    # Voice command examples
    with st.expander("🎯 Voice Command Examples"):
        st.markdown("""
        **Search Commands:**
        - "Search for travel backpack"
        - "Find power adapter"
        - "Look for luggage"
        
        **Cart Commands:**
        - "Show my cart"
        - "Clear cart"
        - "View cart"
        
        **Checkout Commands:**
        - "Proceed to checkout"
        - "Place order"
        
        **General:**
        - "Help"
        - "Hello"
        """)
    
    st.divider()
    
    # Country selection
    countries = sorted([(country.alpha_2, country.name) for country in pycountry.countries], key=lambda x: x[1])
    country_dict = {name: code for code, name in countries}
    country_names = list(country_dict.keys())
    default_country = detect_country()
    default_name = next((name for name, code in country_dict.items() if code == default_country), "United States")
    selected_country = st.selectbox("🌍 Select your country", country_names, index=country_names.index(default_name))
    user_country = country_dict[selected_country]

    # Search section
    st.subheader("🔍 Product Search")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input("What are you looking for?", 
                             key="shopping_query", 
                             placeholder="e.g., travel backpack, power adapter, luggage")
    
    with col2:
        platform = st.selectbox("Platform", ["eBay", "AliExpress", "Both"], key="platform_select")

    # Cart status in sidebar
    with st.sidebar:
        st.subheader("🛍️ Cart Status")
        if st.session_state.cart:
            st.write(f"Items in cart: {len(st.session_state.cart)}")
            total_price = sum(float(item['price']) if str(item['price']).replace('.', '', 1).isdigit() else 0 
                            for item in st.session_state.cart)
            st.write(f"Total: ${total_price:.2f}")
        else:
            st.write("Cart is empty")
        
        if st.button("View Cart", key="sidebar_cart"):
            st.session_state.checkout_stage = "cart"
            st.rerun()

    # Recommended searches
    if "user_id" in st.session_state:
        recommended = get_recommended_searches(st.session_state.user_id)
        if recommended:
            with st.expander("✨ Your Recommended Searches"):
                cols = st.columns(len(recommended))
                for idx, rec in enumerate(recommended):
                    with cols[idx]:
                        if st.button(f"{rec['query']} ({rec['search_count']}×)", 
                                   key=f"rec_{idx}"):
                            st.session_state.shopping_query = rec['query']
                            st.session_state.platform_select = "Both"
                            st.rerun()

    # Auto-search trigger (from voice commands)
    if hasattr(st.session_state, 'auto_search') and st.session_state.auto_search and query:
        st.session_state.auto_search = False
        with st.spinner(f"Searching {platform} for '{query}' in {user_country}..."):
            products = search_products(query, platform, user_country)
            total_results = len(products['ebay']) + len(products['aliexpress'])
            
            if total_results > 0:
                st.session_state.current_products = products
                st.session_state.last_search_query = query
                
                if "user_id" in st.session_state:
                    store_product_search(st.session_state.user_id, query, platform, total_results)
                
                st.success(f"Found {total_results} products!")
                # Update voice response with search results
                updated_response = f"Found {total_results} products for {query}. Here are the results!"
                st.session_state.voice_response = updated_response
                
                # Generate audio for updated response
                audio_data = text_to_speech(updated_response)
                if audio_data:
                    st.session_state.audio_response = audio_data
            else:
                st.warning("No products found. Try different keywords.")
                updated_response = f"No products found for {query}. Try different keywords."
                st.session_state.voice_response = updated_response
                
                # Generate audio for updated response
                audio_data = text_to_speech(updated_response)
                if audio_data:
                    st.session_state.audio_response = audio_data

    # Search button
    if st.button("🔍 Search Products", key="search_products_btn", type="primary"):
        if not query.strip():
            st.warning("Please enter a search term")
        else:
            with st.spinner(f"Searching {platform} for '{query}' in {user_country}..."):
                products = search_products(query, platform, user_country)
                total_results = len(products['ebay']) + len(products['aliexpress'])
                
                if total_results > 0:
                    st.session_state.current_products = products
                    st.session_state.last_search_query = query
                    
                    if "user_id" in st.session_state:
                        store_product_search(st.session_state.user_id, query, platform, total_results)
                    
                    st.success(f"Found {total_results} products!")
                    st.session_state.voice_response = f"Found {total_results} products for {query}"
                else:
                    st.warning("No products found. Try different keywords.")
                    st.session_state.voice_response = f"No products found for {query}. Try different keywords."

    # Display current products (persistent)
    if st.session_state.current_products['ebay'] or st.session_state.current_products['aliexpress']:
        st.subheader(f"📦 Results for '{st.session_state.last_search_query}'")
        display_products(st.session_state.current_products, platform)

    # Handle different checkout stages
    if st.session_state.checkout_stage == "cart":
        view_cart_tab()
    elif st.session_state.checkout_stage == "checkout":
        checkout_tab()

def display_products(products, platform):
    """Display products with improved UI and working cart functionality"""
    
    if platform in ["eBay", "Both"] and products['ebay']:
        st.subheader("💰 eBay Results")
        for idx, product in enumerate(products['ebay']):
            price = product.get('price', {})
            price_value = price.get('value', 'N/A') if isinstance(price, dict) else str(price) if price else 'N/A'
            title = product.get('title', 'No title')
            url = product.get('itemUrl', '#')
            
            # Clean price value
            if isinstance(price_value, str):
                price_value = price_value.replace('$', '').replace(',', '').strip()
            
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    modern_card(
                        title=title,
                        content=f"""
                        **Price:** ${price_value}  
                        **Platform:** eBay  
                        [View Product]({url})
                        """,
                        icon="🛒"
                    )
                
                with col2:
                    if st.button(f"➕ Add to Cart", key=f"add_ebay_{idx}_{url[:10]}"):
                        product_data = {
                            "title": title,
                            "price": price_value,
                            "platform": "eBay",
                            "url": url
                        }
                        add_to_cart(product_data)
                        
                        # Voice feedback for adding to cart
                        cart_response = f"Added {title} to your cart!"
                        st.session_state.voice_response = cart_response
                        audio_data = text_to_speech(cart_response)
                        if audio_data:
                            st.session_state.audio_response = audio_data
                        
                        st.rerun()

    if platform in ["AliExpress", "Both"] and products['aliexpress']:
        st.subheader("🌏 AliExpress Results")
        for idx, product in enumerate(products['aliexpress']):
            price = product.get('price', {})
            price_value = price.get('value', 'N/A') if isinstance(price, dict) else str(price) if price else 'N/A'
            title = product.get('title', 'No title')
            url = product.get('itemUrl', '#')
            
            # Clean price value
            if isinstance(price_value, str):
                price_value = price_value.replace('$', '').replace(',', '').strip()
            
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    modern_card(
                        title=title,
                        content=f"""
                        **Price:** ${price_value}  
                        **Platform:** AliExpress  
                        [View Product]({url})
                        """,
                        icon="🚢"
                    )
                
                with col2:
                    if st.button(f"➕ Add to Cart", key=f"add_ali_{idx}_{url[:10]}"):
                        product_data = {
                            "title": title,
                            "price": price_value,
                            "platform": "AliExpress",
                            "url": url
                        }
                        add_to_cart(product_data)
                        
                        # Voice feedback for adding to cart
                        cart_response = f"Added {title} to your cart!"
                        st.session_state.voice_response = cart_response
                        audio_data = text_to_speech(cart_response)
                        if audio_data:
                            st.session_state.audio_response = audio_data
                        
                        st.rerun()

def view_cart_tab():
    """Display cart with improved UI"""
    st.subheader("🛍️ Your Shopping Cart")
    
    if not st.session_state.cart:
        st.info("Your cart is empty. Add some products to get started!")
        if st.button("← Back to Shopping"):
            st.session_state.checkout_stage = None
            st.rerun()
        return

    # Cart items
    total = 0
    for i, item in enumerate(st.session_state.cart):
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{item['title']}**")
                st.write(f"Platform: {item['platform']}")
                st.write(f"[View Product]({item['url']})")
            
            with col2:
                price = float(item['price']) if str(item['price']).replace('.', '', 1).isdigit() else 0
                st.write(f"**${price:.2f}**")
                total += price
            
            with col3:
                if st.button(f"🗑️ Remove", key=f"remove_{i}"):
                    st.session_state.cart.pop(i)
                    st.session_state.voice_response = f"Removed {item['title']} from cart"
                    st.rerun()
        
        st.divider()

    # Cart summary
    st.subheader(f"💰 Total: ${total:.2f}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("← Continue Shopping"):
            st.session_state.checkout_stage = None
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear Cart"):
            st.session_state.cart.clear()
            st.session_state.voice_response = "Cart cleared"
            st.rerun()
    
    with col3:
        if st.button("✅ Proceed to Checkout", type="primary"):
            st.session_state.checkout_stage = "checkout"
            st.rerun()

def checkout_tab():
    """Checkout process with voice feedback"""
    st.subheader("💳 Checkout")
    # Order summary
    total = sum(float(item['price']) if str(item['price']).replace('.', '', 1).isdigit() else 0 
                for item in st.session_state.cart)
    st.write(f"**Order Summary:** {len(st.session_state.cart)} items - Total: ${total:.2f}")
    
    # Customer details
    with st.form("checkout_form"):
        st.subheader("📝 Shipping Information")
        name = st.text_input("Full Name *", placeholder="Enter your full name")
        email = st.text_input("Email *", placeholder="Enter your email address")
        phone = st.text_input("Phone Number", placeholder="Enter your phone number")
        address = st.text_area("Shipping Address *", placeholder="Enter your complete shipping address")
        
        st.subheader("💳 Payment Method")
        payment_method = st.selectbox("Payment Method", ["Credit Card", "PayPal", "Bank Transfer"])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("← Back to Cart"):
                st.session_state.checkout_stage = "cart"
                st.rerun()
        
        with col2:
            if st.form_submit_button("🛒 Place Order", type="primary"):
                if name and email and address:
                    # Simulate order placement
                    order_id = str(uuid.uuid4())[:8].upper()
                    
                    st.success(f"🎉 Order Placed Successfully!")
                    st.info(f"""
                    **Order ID:** {order_id}  
                    **Customer:** {name}  
                    **Email:** {email}  
                    **Total:** ${total:.2f}  
                    **Items:** {len(st.session_state.cart)}
                    """)
                    
                    # Voice feedback
                    st.session_state.voice_response = f"Order {order_id} placed successfully! Total amount ${total:.2f}"
                    
                    # Clear cart and reset
                    st.session_state.cart.clear()
                    st.session_state.checkout_stage = None
                    st.balloons()
                    
                    if st.button("🛒 Continue Shopping"):
                        st.rerun()
                else:
                    st.error("Please fill in all required fields marked with *")
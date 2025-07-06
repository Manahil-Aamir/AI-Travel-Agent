# Shopping functionality
import streamlit as st
import requests
from components.ui_utils import modern_card
from config import RAPIDAPI_KEY, THEME

def shopping_tab(voice_input=None):
    st.header("🛒 Travel Shopping")
    
    if voice_input:
        modern_card("Voice Input", f"You said: {voice_input}", "🎤")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("What are you looking for?", "travel backpack")
    with col2:
        platform = st.selectbox("Platform", ["eBay", "AliExpress", "Both"])
    
    if st.button("Search Products", key="product_search"):
        with st.spinner("Finding products..."):
            products = search_products(query, platform)
            st.session_state.products = products
            
            if products['ebay'] or products['aliexpress']:
                st.success(f"Found {len(products['ebay']) + len(products['aliexpress'])} products")
                display_products(products, platform)
            else:
                st.warning("No products found")

def search_products(query, platform):
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
            url = "https://aliexpress-datahub.p.rapidapi.com/item_search"
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": "aliexpress-datahub.p.rapidapi.com"
            }
            params = {"q": query, "page": "1"}
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                products['aliexpress'] = response.json().get('result', {}).get('resultList', [])[:5]
        except Exception as e:
            st.error(f"AliExpress search error: {str(e)}")
    
    return products

def display_products(products, platform):
    if platform in ["eBay", "Both"] and products['ebay']:
        st.subheader("eBay Results")
        for product in products['ebay']:
            modern_card(
                product.get('title', 'No title'),
                f"""
                💰 **Price:** ${product.get('price', {}).get('value', 'N/A')}  
                🚚 **Shipping:** ${product.get('shipping', {}).get('cost', {}).get('value', 'N/A')}  
                🔗 [View on eBay]({product.get('itemUrl', '#')})
                """,
                "🛒"
            )
    
    if platform in ["AliExpress", "Both"] and products['aliexpress']:
        st.subheader("AliExpress Results")
        for product in products['aliexpress']:
            modern_card(
                product.get('title', 'No title'),
                f"""
                💰 **Price:** ${product.get('price', {}).get('value', 'N/A')}  
                ⭐ **Rating:** {product.get('rating', 'N/A')} ({product.get('orders', 'N/A')} orders)  
                🔗 [View on AliExpress]({product.get('itemUrl', '#')})
                """,
                "🛍️"
            )
# UI helper functions
import streamlit as st
from config import THEME

print("ui_utils.py loaded")

def set_custom_theme():
    st.markdown(f"""
    <style>
        /* Main Theme */
        :root {{
            --primary: {THEME['primary']};
            --secondary: {THEME['secondary']};
            --accent: {THEME['accent']};
            --dark: {THEME['dark']};
            --light: {THEME['light']};
            --card-bg: {THEME['card_bg']};
            --card-border: {THEME['card_border']};
        }}
        
        [data-theme="dark"] {{
            --dark: {THEME['light']};
            --light: {THEME['dark']};
            --card-bg: rgba(30, 30, 30, 0.95);
            --card-border: rgba(108, 99, 255, 0.4);
        }}
        
        .stApp {{
            background: linear-gradient(135deg, var(--light) 0%, #e6e9f0 100%);
            color: var(--dark);
        }}
        
        /* Cards */
        .modern-card {{
            background: var(--card-bg);
            border-radius: 16px;
            padding: 20px;
            margin: 12px 0;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            border: 1px solid var(--card-border);
            transition: all 0.3s ease;
        }}
        
        .modern-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
        }}
        
        /* Buttons */
        .modern-btn {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 24px;
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        
        .modern-btn:hover {{
            transform: scale(1.02);
            box-shadow: 0 5px 15px rgba(108, 99, 255, 0.3);
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: linear-gradient(135deg, var(--light) 0%, #e6e9f0 100%);
            border-right: 1px solid rgba(108, 99, 255, 0.1);
        }}
        
        /* Tabs */
        .modern-tab {{
            border-radius: 12px !important;
            padding: 10px 16px !important;
            margin: 5px 0 !important;
            background: rgba(255, 255, 255, 0.7) !important;
        }}
        
        .modern-tab[aria-selected="true"] {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%) !important;
            color: white !important;
        }}
    </style>
    """, unsafe_allow_html=True)

def modern_card(title, content, icon=None):
    icon_html = f"<span style='font-size:24px;margin-right:8px;'>{icon}</span>" if icon else ""
    st.markdown(f"""
    <div class="modern-card">
        <h3>{icon_html}{title}</h3>
        {content}
    </div>
    """, unsafe_allow_html=True)
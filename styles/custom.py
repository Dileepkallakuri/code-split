import streamlit as st

def apply_styles():
    """Apply custom CSS styles to the app"""
    st.markdown("""
    <style>
        /* Remove the gray area above the welcome message */
        .stApp {
            background-color: #0e1117; /* Match the dark theme background */
        }
        
        .login-box {
            margin: 0 auto;
            margin-top: 50px; /* Adjust this to control space at the top */
            width: 320px;
            background: #1e1e1e;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 0 10px rgba(255,255,255,0.1);
        }
        .login-box h2 {
            color: #21c55d;
        }
        /* Hide Streamlit branding and hamburger menu */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        /* Improve form spacing */
        .stTextInput, .stSelectbox, .stDateInput, .stNumberInput {
            margin-bottom: 10px;
        }
        /* Center login elements */
        div[data-testid="column"] {
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        /* Force dropdown to show all options without scrolling */
        div[data-baseweb="select"] {
            min-height: 38px !important;
        }
        
        /* Make dropdown list taller */
        div[data-baseweb="select"] ul,
        div[data-baseweb="menu"],
        div[role="listbox"] {
            max-height: 600px !important;
            overflow-y: visible !important;
        }
        
        /* Ensure dropdown opens upward if needed to show all options */
        div[data-baseweb="popover"] {
            z-index: 999 !important;
            position: relative !important;
        }
        
        /* Keep dropdown open and visible */
        div[data-baseweb="select"] div[data-testid="stSelectbox"] {
            height: auto !important;
            max-height: none !important;
        }
        
        /* Alternative approach: make the select box itself taller */
        .stSelectbox > div:first-child {
            height: auto !important;
            padding-bottom: 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)
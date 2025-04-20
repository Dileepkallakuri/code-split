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
        
        /* Fix dropdown height to show all options */
        div[data-baseweb="select"] ul {
            max-height: 400px !important;
        }
        
        /* Ensure the dropdown options are all visible */
        .stSelectbox div[data-baseweb="popover"] {
            max-height: none !important;
        }
        
        .stSelectbox div[data-baseweb="select"] div[data-baseweb="menu"] {
            max-height: 400px !important;
        }
        
        /* Make the dropdown list wider and ensure it's visible in the view */
        div[role="listbox"] {
            max-height: 400px !important;
            z-index: 999 !important;
        }
    </style>
    """, unsafe_allow_html=True)
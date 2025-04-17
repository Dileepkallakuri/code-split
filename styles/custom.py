import streamlit as st

def apply_styles():
    """Apply custom CSS styles to the app"""
    st.markdown("""
    <style>
        .login-box {
            margin: 0 auto;
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
    </style>
    """, unsafe_allow_html=True)
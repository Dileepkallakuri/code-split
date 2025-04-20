import streamlit as st
from utils.auth import check_credentials, login_screen, show_sidebar_header, show_sidebar_footer
from utils.helpers import load_app_module
from styles.custom import apply_styles

# Set page config
st.set_page_config(page_title="Dileep Apps Space", page_icon="🤩", layout="wide")

# Apply custom CSS
apply_styles()

# Initialize session state variables
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.auth_username = ""
if "selected_app" not in st.session_state:
    st.session_state.selected_app = None
if "selected_db_tool" not in st.session_state:
    st.session_state.selected_db_tool = None

# Available apps
AVAILABLE_APPS = [
    "📈 Crypto Trade Tracker",
    "📊 Stocks Journal",
    "🗄️ Database & Cloud",
    "🗓️ Daily Expense Tracker",
    "🛫 Travel Itinerary Planner",
    "💡 SparkStorm & IdeaFlow",
    "📝 YouTube Transcript Downloader",
    "🥇 Gold Price Live"
]

# ---- Login Screen ----
if not st.session_state.authenticated:
    login_screen()
    st.stop()

# ---- Post Login: Greet & Choose App ----
if not st.session_state.selected_app:
    st.markdown(f"### 👋 Welcome, **{st.session_state.auth_username}**!")
    st.markdown("Please choose an app to continue:")

    selected = st.selectbox("📂 Choose App", AVAILABLE_APPS)

    if st.button("Launch App"):
        st.session_state.selected_app = selected
        st.rerun()
    st.stop()

# ---- Sidebar Header ----
app_mode = st.session_state.selected_app
show_sidebar_header()

# ---- Load the appropriate app module ----
# App functions will be displayed here in the sidebar
load_app_module(app_mode)

# ---- Sidebar Footer with App Switcher and Logout ----
show_sidebar_footer(app_mode, AVAILABLE_APPS)
import streamlit as st
from utils.auth import check_credentials, login_screen, show_sidebar
from utils.helpers import load_app_module
from styles.custom import apply_styles

# Apply custom CSS
apply_styles()

# Set page config
st.set_page_config(page_title="Dileep Apps Space", page_icon="🛠️", layout="wide")

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
    "📝 YouTube Transcript Downloader",
    "🗓️ Daily Expense Tracker",
    "🥇 Gold Price Live",
    "💡 SparkStorm & IdeaFlow"
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

# ---- Sidebar with App Switcher and Logout ----
app_mode = st.session_state.selected_app
show_sidebar(app_mode, AVAILABLE_APPS)

# ---- Load the appropriate app module ----
load_app_module(app_mode)
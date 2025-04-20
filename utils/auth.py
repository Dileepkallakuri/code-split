import streamlit as st

# ---- Users ----
USERS = {
    "admin": "pass123",
    "Dileep": "1234",
    "Prasanna": "97045",
    "Kalyan": "123",
    "Naresh": "123",
    "Rohit": "5353"
}

def check_credentials(username, password):
    """Validate user credentials"""
    return USERS.get(username) == password

def login_screen():
    """Display login screen"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("### 👋 Hi, Welcome to the **Dileep Apps Space**!")
        st.write("Please enter your credentials to continue.")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if check_credentials(username, password):
                st.session_state.authenticated = True
                st.session_state.auth_username = username
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
        st.markdown("</div>", unsafe_allow_html=True)

def show_sidebar_header():
    """Display just the header portion of the sidebar"""
    st.sidebar.title("Dileep Apps Space")
    st.sidebar.markdown(f"👤 Logged in as **{st.session_state.auth_username}**")
    st.sidebar.markdown("---")
    
    # App-specific functions will be added here by the individual app

def show_sidebar_footer(app_mode, available_apps):
    """Display the footer portion of the sidebar with app switching options"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("Switch App")
    new_app = st.sidebar.radio("Select App", available_apps, 
                            index=available_apps.index(app_mode))

    if new_app != app_mode:
        st.session_state.selected_app = new_app
        # Reset any sub-selections when switching apps
        if new_app == "🗄️ Database & Cloud":
            st.session_state.selected_db_tool = None
        st.rerun()

    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.selected_app = None
        st.session_state.selected_db_tool = None
        st.rerun()

def show_sidebar(app_mode, available_apps):
    """For backwards compatibility - this will call both header and footer"""
    show_sidebar_header()
    show_sidebar_footer(app_mode, available_apps)

import importlib
import streamlit as st

def load_app_module(app_mode):
    """Dynamically load the appropriate app module based on the selected app"""
    app_mapping = {
        "📈 Crypto Trade Tracker": "apps.crypto_tracker",
        "📊 Stocks Journal": "apps.stocks_journal",
        "🗄️ Database & Cloud": "apps.database_cloud",
        "📝 YouTube Transcript Downloader": "apps.youtube_downloader",
        "🗓️ Daily Expense Tracker": "apps.expense_tracker",
        "🥇 Gold Price Live": "apps.gold_price",
        "💡 SparkStorm & IdeaFlow": "apps.sparkstorm"
    }
    
    module_name = app_mapping.get(app_mode)
    if not module_name:
        st.error(f"App module not found for: {app_mode}")
        return
    
    try:
        # Using importlib to dynamically import the correct module
        module = importlib.import_module(module_name)
        # Call the main function of the module
        module.main()
    except ImportError as e:
        st.error(f"Failed to import module {module_name}: {e}")
    except AttributeError:
        st.error(f"Module {module_name} does not have a main() function")
    except Exception as e:
        st.error(f"Error loading app {app_mode}: {e}")
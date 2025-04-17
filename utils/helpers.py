import importlib
import streamlit as st

def load_app_module(app_mode):
    """Dynamically load the appropriate app module based on the selected app"""
    app_mapping = {
        "📈 Crypto Trade Tracker": ("apps.crypto_tracker", "main"),
        "📊 Stocks Journal": ("apps.stocks_journal", "show_stocks_journal"),
        "🗄️ Database & Cloud": ("apps.database_cloud", "show_database_cloud"),
        "📝 YouTube Transcript Downloader": ("apps.youtube_downloader", "show_youtube_downloader"),
        "🗓️ Daily Expense Tracker": ("apps.expense_tracker", "show_expense_tracker"),
        "🥇 Gold Price Live": ("apps.gold_price", "show_gold_price"),
        "💡 SparkStorm & IdeaFlow": ("apps.sparkstorm", "show_sparkstorm")
    }
    
    if app_mode not in app_mapping:
        st.error(f"App module not found for: {app_mode}")
        return
    
    module_name, function_name = app_mapping[app_mode]
    
    try:
        # Using importlib to dynamically import the correct module
        module = importlib.import_module(module_name)
        # Get the correct function to call
        func = getattr(module, function_name)
        # Call the function
        func()
    except ImportError as e:
        st.error(f"Failed to import module {module_name}: {e}")
    except AttributeError as e:
        st.error(f"Module {module_name} does not have the required function {function_name}(): {e}")
    except Exception as e:
        st.error(f"Error loading app {app_mode}: {e}")
# apps/travel_planner.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import uuid

def show_travel_planner():
    st.title("🧳 Travel Itinerary Planner")
    add_timeline_styles()
    
    # Create data directory if it doesn't exist
    if not os.path.exists("data"):
        os.makedirs("data")
    
    # Initialize itineraries file if it doesn't exist
    itineraries_file = "data/travel_itineraries.json"
    if not os.path.exists(itineraries_file):
        with open(itineraries_file, "w") as f:
            json.dump({"itineraries": []}, f)
    
    # Load existing itineraries
    with open(itineraries_file, "r") as f:
        data = json.load(f)
        itineraries = data["itineraries"]
    
    # Initialize session state variables
    if "active_itinerary" not in st.session_state:
        st.session_state.active_itinerary = None
    if "editing_activity" not in st.session_state:
        st.session_state.editing_activity = None
    
    # Function to save itineraries
    def save_itineraries():
        with open(itineraries_file, "w") as f:
            json.dump({"itineraries": itineraries}, f, indent=4)
    
    # Sidebar options
    action = st.sidebar.radio("Action", ["View Itineraries", "Create New Itinerary"])
    
    if action == "Create New Itinerary":
        create_new_itinerary()
    else:
        view_itineraries(itineraries, save_itineraries)
    
def create_new_itinerary():
    st.header("Create New Itinerary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        trip_name = st.text_input("Trip Name", "Trip 1")
        destination = st.text_input("Destination", "")
    
    with col2:
        start_date = st.date_input("Start Date", datetime.now())
        end_date = st.date_input("End Date", datetime.now() + timedelta(days=3))
    
    if st.button("Create Itinerary"):
        if trip_name and destination and start_date <= end_date:
            # Create new itinerary object
            new_itinerary = {
                "id": str(uuid.uuid4()),
                "name": trip_name,
                "destination": destination,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "activities": []
            }
            
            # Load existing itineraries
            itineraries_file = "data/travel_itineraries.json"
            with open(itineraries_file, "r") as f:
                data = json.load(f)
                itineraries = data["itineraries"]
            
            # Add new itinerary and save
            itineraries.append(new_itinerary)
            with open(itineraries_file, "w") as f:
                json.dump({"itineraries": itineraries}, f, indent=4)
            
            st.success(f"Itinerary '{trip_name}' created successfully!")
            st.session_state.active_itinerary = new_itinerary["id"]
            st.rerun()
        else:
            st.error("Please fill all fields and ensure end date is after start date.")

def view_itineraries(itineraries, save_callback):
    if not itineraries:
        st.info("No itineraries found. Create one to get started!")
        return
    
    # Display list of itineraries
    st.header("Your Itineraries")
    
    itinerary_names = [f"{i['name']} ({i['destination']} - {i['start_date']} to {i['end_date']})" for i in itineraries]
    itinerary_ids = [i["id"] for i in itineraries]
    
    selected_idx = 0
    if st.session_state.active_itinerary:
        if st.session_state.active_itinerary in itinerary_ids:
            selected_idx = itinerary_ids.index(st.session_state.active_itinerary)
    
    selected_itinerary_name = st.selectbox("Select Itinerary", itinerary_names, index=selected_idx)
    selected_idx = itinerary_names.index(selected_itinerary_name)
    st.session_state.active_itinerary = itineraries[selected_idx]["id"]
    
    # Get the selected itinerary
    active_itinerary = next((i for i in itineraries if i["id"] == st.session_state.active_itinerary), None)
    
    if active_itinerary:
        # Display itinerary details
        st.subheader(f"{active_itinerary['name']} - {active_itinerary['destination']}")
        st.write(f"**Date:** {active_itinerary['start_date']} to {active_itinerary['end_date']}")
        
        # Calculate number of days in the trip
        start = datetime.strptime(active_itinerary['start_date'], "%Y-%m-%d")
        end = datetime.strptime(active_itinerary['end_date'], "%Y-%m-%d")
        days = (end - start).days + 1
        
        # Section for adding new activities
        with st.expander("Add New Activity", expanded=False):
            add_new_activity(active_itinerary, days, itineraries, save_callback)
        
        # Display activities by day
        display_activities_by_day(active_itinerary, days, start, itineraries, save_callback)
        
        # Delete itinerary button
        if st.button("Delete This Itinerary", key="delete_itinerary"):
            itineraries.remove(active_itinerary)
            save_callback()
            st.session_state.active_itinerary = None
            st.success("Itinerary deleted successfully!")
            st.rerun()

def add_new_activity(itinerary, days, itineraries, save_callback):
    st.subheader("Add New Activity")
    
    col1, col2 = st.columns(2)
    
    with col1:
        day_num = st.selectbox("Day", list(range(1, days + 1)))
        activity_type = st.selectbox("Activity Type", [
            "Transportation", "Accommodation", "Sightseeing", "Food", "Meeting", 
            "Activity", "Rest", "Other"
        ])
        
    with col2:
        activity_time = st.time_input("Time", datetime.strptime("09:00", "%H:%M").time())
        activity_duration = st.number_input("Duration (minutes)", min_value=15, value=60, step=15)
    
    activity_name = st.text_input("Activity Name", "")
    activity_location = st.text_input("Location/Address", "")
    notes = st.text_area("Notes", "")
    
    if st.button("Add Activity"):
        if activity_name:
            # Calculate activity date
            start_date = datetime.strptime(itinerary['start_date'], "%Y-%m-%d")
            activity_date = start_date + timedelta(days=day_num - 1)
            
            # Create activity object
            new_activity = {
                "id": str(uuid.uuid4()),
                "name": activity_name,
                "type": activity_type,
                "time": activity_time.strftime("%H:%M"),
                "duration": activity_duration,
                "location": activity_location,
                "notes": notes,
                "day": day_num,
                "date": activity_date.strftime("%Y-%m-%d")
            }
            
            # Add to itinerary
            itinerary["activities"].append(new_activity)
            save_callback()
            st.success(f"Activity '{activity_name}' added successfully!")
        else:
            st.error("Please enter an activity name.")

def display_activities_by_day(itinerary, days, start_date, itineraries, save_callback):
    activities = itinerary.get("activities", [])
    
    # Group activities by day
    activities_by_day = {}
    for day in range(1, days + 1):
        day_date = start_date + timedelta(days=day - 1)
        day_str = day_date.strftime("%A, %d %B %Y")
        activities_by_day[day] = {
            "date_str": day_str,
            "activities": [a for a in activities if a["day"] == day]
        }
        # Sort activities by time
        activities_by_day[day]["activities"].sort(key=lambda x: x["time"])
    
    # Display activities for each day with tabs
    tabs = st.tabs([f"Day {day}" for day in range(1, days + 1)])
    
    for day, tab in enumerate(tabs, 1):
        with tab:
            st.markdown(f"<h2 style='color: #4CAF50;'>{activities_by_day[day]['date_str']}</h2>", unsafe_allow_html=True)
            
            day_activities = activities_by_day[day]["activities"]
            if not day_activities:
                st.info(f"No activities planned for Day {day} yet.")
            else:
                # Create a container for the timeline
                timeline_container = st.container()
                
                with timeline_container:
                    for i, activity in enumerate(day_activities):
                        # Start of timeline item
                        col1, col2 = st.columns([1, 5])
                        
                        with col1:
                            # Time column
                            st.markdown(f"""
                            <div style='text-align: right; padding-right: 15px; position: relative;'>
                                <div style='font-weight: bold; font-size: 18px; color: #E0E0E0;'>{activity['time']}</div>
                                <div style='position: absolute; top: 0; right: -10px; width: 20px; height: 20px; 
                                           border-radius: 50%; background-color: #2196F3; z-index: 2;'></div>
                                {'<div style="position: absolute; top: 20px; right: -1px; height: 100%; width: 2px; background-color: #555; z-index: 1;"></div>' 
                                if i < len(day_activities) - 1 else ''}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            # Activity details in a card
                            icon = get_activity_icon(activity['type'])
                            activity_color = get_activity_color(activity['type'])
                            
                            st.markdown(f"""
                            <div style='background-color: #1E1E2E; border-radius: 10px; padding: 15px; 
                                       margin-bottom: 20px; border-left: 4px solid {activity_color};'>
                                <div style='display: flex; justify-content: space-between; align-items: center;'>
                                    <div>
                                        <div style='font-size: 16px; font-weight: bold;'>
                                            {icon} {activity['name']} <span style='color: #888; font-weight: normal;'>({activity['duration']} min)</span>
                                        </div>
                                        <div style='font-size: 14px; color: #888; margin-top: 5px;'>
                                            {activity['type']}
                                        </div>
                                    </div>
                                    <div>
                                        <button onclick="document.getElementById('edit_{activity['id']}').click();" 
                                                style='background: none; border: 1px solid #555; color: #E0E0E0; 
                                                        border-radius: 4px; padding: 3px 8px; margin-right: 5px; cursor: pointer;'>
                                            Edit
                                        </button>
                                        <button onclick="document.getElementById('delete_{activity['id']}').click();" 
                                                style='background: none; border: 1px solid #555; color: #E0E0E0; 
                                                        border-radius: 4px; padding: 3px 8px; cursor: pointer;'>
                                            Delete
                                        </button>
                                    </div>
                                </div>
                                
                                {f'<div style="margin-top: 8px;"><span style="color: #888;">📍</span> {activity["location"]}</div>' if activity['location'] else ''}
                                {f'<div style="margin-top: 8px; font-style: italic; color: #888;">Note: {activity["notes"]}</div>' if activity['notes'] else ''}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Hidden buttons for Streamlit to handle
                            if st.button("Edit", key=f"edit_{activity['id']}", help="Edit this activity"):
                                st.session_state.editing_activity = activity["id"]
                                st.rerun()
                            if st.button("Delete", key=f"delete_{activity['id']}", help="Delete this activity"):
                                itinerary["activities"].remove(activity)
                                save_callback()
                                st.success("Activity deleted!")
                                st.rerun()
            
            # Edit activity form (same as before)
            if st.session_state.editing_activity:
                edit_activity = next((a for a in day_activities if a["id"] == st.session_state.editing_activity), None)
                if edit_activity:
                    st.markdown("---")
                    st.subheader("Edit Activity")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_day = st.selectbox("Day", list(range(1, days + 1)), index=edit_activity["day"]-1, key="edit_day")
                        edit_type = st.selectbox("Activity Type", [
                            "Transportation", "Accommodation", "Sightseeing", "Food", "Meeting", 
                            "Activity", "Rest", "Other"
                        ], index=["Transportation", "Accommodation", "Sightseeing", "Food", "Meeting", 
                            "Activity", "Rest", "Other"].index(edit_activity["type"]), key="edit_type")
                    
                    with col2:
                        edit_time = st.time_input("Time", datetime.strptime(edit_activity["time"], "%H:%M").time(), key="edit_time")
                        edit_duration = st.number_input("Duration (minutes)", min_value=15, value=edit_activity["duration"], step=15, key="edit_duration")
                    
                    edit_name = st.text_input("Activity Name", edit_activity["name"], key="edit_name")
                    edit_location = st.text_input("Location/Address", edit_activity["location"], key="edit_location")
                    edit_notes = st.text_area("Notes", edit_activity["notes"], key="edit_notes")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save Changes"):
                            # Update activity
                            edit_activity["name"] = edit_name
                            edit_activity["type"] = edit_type
                            edit_activity["time"] = edit_time.strftime("%H:%M")
                            edit_activity["duration"] = edit_duration
                            edit_activity["location"] = edit_location
                            edit_activity["notes"] = edit_notes
                            edit_activity["day"] = edit_day
                            
                            # Calculate new date based on day
                            activity_date = start_date + timedelta(days=edit_day - 1)
                            edit_activity["date"] = activity_date.strftime("%Y-%m-%d")
                            
                            save_callback()
                            st.session_state.editing_activity = None
                            st.success("Activity updated successfully!")
                            st.rerun()
                    
                    with col2:
                        if st.button("Cancel Editing"):
                            st.session_state.editing_activity = None
                            st.rerun()

def get_activity_icon(activity_type):
    icons = {
        "Transportation": "🚗",
        "Accommodation": "🏨",
        "Sightseeing": "🏛️",
        "Food": "🍽️",
        "Meeting": "👥",
        "Activity": "🏄‍♂️",
        "Rest": "😴",
        "Other": "📝"
    }
    return icons.get(activity_type, "📌")

def get_activity_color(activity_type):
    colors = {
        "Transportation": "#2196F3",  # Blue
        "Accommodation": "#9C27B0",   # Purple
        "Sightseeing": "#4CAF50",     # Green
        "Food": "#FF9800",            # Orange
        "Meeting": "#E91E63",         # Pink
        "Activity": "#00BCD4",        # Cyan
        "Rest": "#795548",            # Brown
        "Other": "#607D8B"            # Blue Grey
    }
    return colors.get(activity_type, "#607D8B")

def add_timeline_styles():
    st.markdown("""
    <style>
        /* Hide the actual Streamlit buttons that we're using for state management */
        button[data-testid="baseButton-secondary"] {
            display: none;
        }
        
        /* Timeline styling */
        .timeline-content {
            margin-left: 20px;
            padding-left: 20px;
            border-left: 2px solid #555;
            position: relative;
        }
        
        .timeline-dot {
            position: absolute;
            left: -10px;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background-color: #2196F3;
        }
        
        /* Activity card styling */
        .activity-card {
            background-color: #1E1E2E;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            border-left: 4px solid #2196F3;
        }
    </style>
    """, unsafe_allow_html=True)

def export_itinerary(itinerary):
    activities = sorted(itinerary["activities"], key=lambda x: (x["day"], x["time"]))
    
    # Create DataFrame for export
    df = pd.DataFrame(activities)
    return df

if __name__ == "__main__":
    show_travel_planner()
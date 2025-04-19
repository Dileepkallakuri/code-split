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
            "Food", "Accommodation", "Sightseeing", "Meeting", 
            "Activity", "Rest", "Transportation", "Other"
        ])
    
    with col2:
        activity_time = st.time_input("Time", datetime.strptime("09:00", "%H:%M").time())
        activity_duration = st.number_input("Duration (minutes)", min_value=15, value=60, step=15)
    
    # If Transportation is selected, show additional options
    transport_type = None
    if activity_type == "Transportation":
        transport_type = st.selectbox("Transport Type", [
            "Flight", "Bus", "Train", "Cab/Taxi", "Ship/Ferry", "Car Rental", "Other"
        ])
    
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
                "transport_type": transport_type if transport_type else None,
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
                for i, activity in enumerate(day_activities):
                    col1, col2 = st.columns([1, 5])
                    
                    with col1:
                        st.markdown(f"<div style='text-align: right; padding-right: 15px; font-weight: bold;'>{activity['time']}</div>", unsafe_allow_html=True)
                    
                    with col2:
                        # Generate the appropriate icon based on activity type
                        icon = get_activity_icon(activity)
                        activity_color = get_activity_color(activity['type'])
                        
                        # Create the activity card
                        with st.container():
                            st.markdown(f"""
                            <div style='background-color: #1E1E2E; border-radius: 10px; padding: 15px; 
                                       margin-bottom: 20px; border-left: 4px solid {activity_color};'>
                                <div style='display: flex; justify-content: space-between; margin-bottom: 8px;'>
                                    <div>
                                        <span style='font-size: 16px; font-weight: bold;'>{icon} {activity['name']}</span>
                                        <span style='color: #888; font-size: 14px;'> ({activity['duration']} min)</span>
                                    </div>
                                </div>

                                <div style='color: #888; font-size: 14px; margin-bottom: 5px;'>
                                    {activity['type']} {f"- {activity['transport_type']}" if activity.get('transport_type') else ""}
                                </div>

                                {f'<div style="margin-top: 8px;"><span style="color: #888;">📍</span> {activity["location"]}</div>' if activity['location'] else ''}
                                {f'<div style="margin-top: 8px; font-style: italic; color: #888;"><span style="color: #888;">📝</span> {activity["notes"]}</div>' if activity['notes'] else ''}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Regular Streamlit buttons for edit and delete
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Edit", key=f"edit_{activity['id']}"):
                                    st.session_state.editing_activity = activity["id"]
                                    st.rerun()
                            with col2:
                                if st.button("Delete", key=f"delete_{activity['id']}"):
                                    itinerary["activities"].remove(activity)
                                    save_callback()
                                    st.success("Activity deleted!")
                                    st.rerun()
            
            # Edit activity form
            if st.session_state.editing_activity:
                edit_activity = next((a for a in activities if a["id"] == st.session_state.editing_activity), None)
                if edit_activity:
                    st.markdown("---")
                    st.subheader("Edit Activity")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_day = st.selectbox("Day", list(range(1, days + 1)), index=edit_activity["day"]-1, key="edit_day")
                        edit_type = st.selectbox("Activity Type", [
                            "Food", "Accommodation", "Sightseeing", "Meeting", 
                            "Activity", "Rest", "Transportation", "Other"
                        ], index=["Food", "Accommodation", "Sightseeing", "Meeting", 
                            "Activity", "Rest", "Transportation", "Other"].index(edit_activity["type"]), key="edit_type")
                    
                    with col2:
                        edit_time = st.time_input("Time", datetime.strptime(edit_activity["time"], "%H:%M").time(), key="edit_time")
                        edit_duration = st.number_input("Duration (minutes)", min_value=15, value=edit_activity["duration"], step=15, key="edit_duration")
                    
                    # If Transportation is selected, show additional options
                    edit_transport_type = None
                    if edit_type == "Transportation":
                        transport_options = ["Flight", "Bus", "Train", "Cab/Taxi", "Ship/Ferry", "Car Rental", "Other"]
                        default_idx = 0
                        if edit_activity.get("transport_type") and edit_activity["transport_type"] in transport_options:
                            default_idx = transport_options.index(edit_activity["transport_type"])
                        edit_transport_type = st.selectbox("Transport Type", transport_options, index=default_idx, key="edit_transport_type")
                    
                    edit_name = st.text_input("Activity Name", edit_activity["name"], key="edit_name")
                    edit_location = st.text_input("Location/Address", edit_activity["location"], key="edit_location")
                    edit_notes = st.text_area("Notes", edit_activity["notes"], key="edit_notes")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save Changes"):
                            # Update activity
                            edit_activity["name"] = edit_name
                            edit_activity["type"] = edit_type
                            edit_activity["transport_type"] = edit_transport_type if edit_transport_type else None
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

def get_activity_icon(activity):
    """Get icon based on activity type with transport-specific icons"""
    if activity['type'] == "Transportation":
        # Transport-specific icons
        transport_type = activity.get('transport_type', '').lower()
        if "flight" in transport_type:
            return "✈️"
        elif "bus" in transport_type:
            return "🚌"
        elif "train" in transport_type:
            return "🚆"
        elif "cab" in transport_type or "taxi" in transport_type:
            return "🚕"
        elif "ship" in transport_type or "ferry" in transport_type:
            return "🚢"
        elif "car" in transport_type:
            return "🚗"
        else:
            return "🚗"
    
    # Standard activity icons
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
    return icons.get(activity['type'], "📌")

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
        
        /* Make buttons look better */  
        .stButton button {
            width: 100%;
            border-radius: 5px;
            padding: 4px 8px;
            font-size: 14px;
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
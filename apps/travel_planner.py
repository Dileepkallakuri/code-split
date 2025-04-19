# apps/travel_planner.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import uuid

def show_travel_planner():
    st.title("🧳 Travel Itinerary Planner")
    
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
    
    # Display activities for each day
    tabs = st.tabs([f"Day {day}" for day in range(1, days + 1)])
    
    for day, tab in enumerate(tabs, 1):
        with tab:
            st.subheader(activities_by_day[day]["date_str"])
            
            day_activities = activities_by_day[day]["activities"]
            if not day_activities:
                st.info(f"No activities planned for Day {day} yet.")
            else:
                for activity in day_activities:
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        st.write(f"**{activity['time']}**")
                        icon = get_activity_icon(activity['type'])
                        st.write(f"{icon} {activity['type']}")
                    
                    with col2:
                        st.write(f"**{activity['name']}**")
                        if activity['location']:
                            st.write(f"📍 {activity['location']}")
                        if activity['notes']:
                            st.write(f"_Note: {activity['notes']}_")
                    
                    with col3:
                        st.write(f"{activity['duration']} min")
                        if st.button("Edit", key=f"edit_{activity['id']}"):
                            st.session_state.editing_activity = activity["id"]
                            st.rerun()
                        if st.button("Delete", key=f"delete_{activity['id']}"):
                            itinerary["activities"].remove(activity)
                            save_callback()
                            st.success("Activity deleted!")
                            st.rerun()
                    
                    st.divider()
            
            # Edit activity form
            if st.session_state.editing_activity:
                edit_activity = next((a for a in day_activities if a["id"] == st.session_state.editing_activity), None)
                if edit_activity:
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

def export_itinerary(itinerary):
    activities = sorted(itinerary["activities"], key=lambda x: (x["day"], x["time"]))
    
    # Create DataFrame for export
    df = pd.DataFrame(activities)
    return df

if __name__ == "__main__":
    show_travel_planner()
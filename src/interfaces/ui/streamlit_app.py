from datetime import datetime, timedelta
import requests
import streamlit as st
from streamlit_calendar import calendar
import logging
import json
from src.core.logger import setup_logger

logger = setup_logger(__name__)

BACKEND_URL = "http://localhost:8000"


def get_system_message(selected_date: datetime) -> dict:
    weekday = selected_date.strftime("%A")
    days_until_friday = 4 - selected_date.weekday()
    if days_until_friday < 0:
        days_until_friday = 0
    end_date = selected_date + timedelta(days=days_until_friday)

    return {
        "role": "system",
        "content": f"""You are a helpful calendar planning assistant.
        The user is planning their calendar:
        - Start date: {selected_date.strftime('%Y-%m-%d')} ({weekday})
        - End date: {end_date.strftime('%Y-%m-%d')} (Friday)
        Important scheduling rules:
        - Begin precisely from {weekday}, {selected_date.strftime('%Y-%m-%d')}
        - End strictly on {end_date.strftime('%Y-%m-%d')}
        - Don't generate any events beyond this Friday
        - Format all dates and times in ISO format (YYYY-MM-DD HH:mm)
        - Only schedule within this specific work week period""",
    }


def chat_input_handler(prompt: str) -> None:
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        try:
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={
                    "messages": st.session_state.messages,
                    "selected_date": st.session_state.selected_date.isoformat(),
                    "functions": get_llm_functions(),  # Add functions to request
                },
            )

            logger.debug(f"API Response: {response.text}")

            if response.status_code == 200:
                handle_chat_response(response.json())
            else:
                st.session_state.query_status = f"Error: {response.text}"
        except Exception as e:
            logger.error(f"Error in chat handler: {str(e)}")
            st.session_state.query_status = f"Error: {str(e)}"


def handle_chat_response(data: dict) -> None:
    if "choices" in data and len(data["choices"]) > 0:
        choice = data["choices"][0]
        message = choice.get("message", {})

        if "function_call" in message:
            handle_function_call(message["function_call"])
        elif "content" in message and message["content"] is not None:
            st.session_state.messages.append(
                {"role": "assistant", "content": message["content"]}
            )
            st.session_state.query_status = "Success"
        else:
            st.session_state.query_status = "Error: Empty response from assistant"
    else:
        st.session_state.query_status = "Error: Invalid response format"


def handle_function_call(function_call: dict) -> None:
    function_name = function_call["name"]
    arguments = json.loads(function_call["arguments"])

    if function_name == "insert_event":
        handle_insert_event(arguments)
    elif function_name == "delete_event":
        handle_delete_event(arguments)
    elif function_name == "get_events":
        handle_get_events()

    st.session_state.query_status = "Success"
    st.rerun()


def handle_insert_event(arguments: dict) -> None:
    response = requests.post(f"{BACKEND_URL}/events", json=arguments)
    if response.status_code == 200:
        st.success("Event added successfully!")
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"I've added the event '{arguments.get('event_name')}' to your calendar.",
            }
        )
    else:
        st.error("Failed to add event")


def handle_delete_event(arguments: dict) -> None:
    event_id = arguments.get("event_id")
    response = requests.delete(f"{BACKEND_URL}/events/{event_id}")
    if response.status_code == 200:
        st.success("Event deleted successfully!")
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "I've deleted the event from your calendar.",
            }
        )
    else:
        st.error("Failed to delete event")


def handle_get_events() -> None:
    response = requests.get(f"{BACKEND_URL}/events")
    if response.status_code == 200:
        events = response.json()
        if events:
            events_text = "Here are your current events:\n"
            for event in events:
                events_text += f"\n- {event['event_name']} from {event['event_start_date_time']} to {event['event_end_date_time']}"
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": events_text,
                }
            )
        else:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": "You have no events scheduled.",
                }
            )
    else:
        st.error("Failed to fetch events")


def display_chat() -> None:
    for message in st.session_state.messages[1:]:  # Skip system message
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def display_events() -> None:
    response = requests.get(f"{BACKEND_URL}/events")
    if response.status_code == 200:
        events = response.json()
        if events:
            for event in events:
                col1, col2 = st.columns([8, 1])
                with col1:
                    st.write(
                        f"**{event['event_name']}** from {event['event_start_date_time']} to {event['event_end_date_time']}"
                    )
                with col2:
                    if st.button("Delete", key=f"delete_{event['id']}"):
                        chat_input_handler(f"Delete event with ID {event['id']}")
        else:
            st.write("No events found")
    else:
        st.error("Failed to fetch events")

def display_events_calendar() -> None:
    response = requests.get(f"{BACKEND_URL}/events")
    if response.status_code == 200:
        events = response.json()
        if events:
            calendar_events = format_events_for_calendar(events)
            calendar_options = {
                "initialDate": "2024-11-13",
                "editable": "false",
                "selectable": "true",
                "headerToolbar": {
                    "left": "today prev,next",
                    "center": "title",
                    "right": "resourceTimelineDay,resourceTimelineWeek,resourceTimelineMonth",
                },
                "slotMinTime": "06:00:00",
                "slotMaxTime": "23:00:00",
                "initialView": "timeGridWeek",
                "resourceGroupField": "building",
                "resources": [
                    {"id": "a", "building": "Building A", "title": "Building A"},
                    {"id": "b", "building": "Building A", "title": "Building B"},
                    {"id": "c", "building": "Building B", "title": "Building C"},
                    {"id": "d", "building": "Building B", "title": "Building D"},
                    {"id": "e", "building": "Building C", "title": "Building E"},
                    {"id": "f", "building": "Building C", "title": "Building F"},
                ]
            }
            css= """
                .fc-event-past {
                    opacity: 0.8;
                }
                .fc-event-time {
                    font-style: italic;
                }
                .fc-event-title {
                    font-weight: 700;
                }
                .fc-toolbar-title {
                    font-size: 2rem;
                }
            """
            
            cal = calendar(events=calendar_events, options=calendar_options, custom_css=css)

            st.write(cal)

        else:
            st.write("No events found")
    else:
        st.error("Failed to fetch events")

def format_events_for_calendar(events):
    formatted_events = []
    for event in events:
        start = event["event_start_date_time"]
        end = event["event_end_date_time"]
        formatted_events.append({
            "title": event["event_name"],
            "start": start,
            "end": end,
            "ressourceId": "a",
        })
    return formatted_events

def get_llm_functions() -> list:
    return [
        {
            "name": "insert_event",
            "description": "Insert a new calendar event",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_name": {
                        "type": "string",
                        "description": "Name of the event",
                    },
                    "event_description": {
                        "type": "string",
                        "description": "Description of the event",
                    },
                    "event_start_date_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Start date and time of the event (ISO format)",
                    },
                    "event_end_date_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "End date and time of the event (ISO format)",
                    },
                    "event_location": {
                        "type": "string",
                        "description": "Location of the event",
                    },
                },
                "required": [
                    "event_name",
                    "event_start_date_time",
                    "event_end_date_time",
                ],
            },
        },
        {
            "name": "get_events",
            "description": "Get all calendar events",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": "delete_event",
            "description": "Delete a calendar event",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "ID of the event to delete",
                    }
                },
                "required": ["event_id"],
            },
        },
    ]


def main():
    st.set_page_config(
        page_title="Calendar Planning Assistant", page_icon="📅", layout="centered"
    )
    st.title("🗓️ Calendar Planning Assistant")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = [get_system_message(datetime.now())]
    if "query_status" not in st.session_state:
        st.session_state.query_status = ""
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = datetime.now()

    # Sidebar
    with st.sidebar:
        st.header("Calendar Context")
        selected_week = st.date_input(
            "Select Week Starting From:", datetime.now().date(), key="date_picker"
        )

        # Gérer les différents types de retour possibles de date_input
        if isinstance(selected_week, tuple):
            if len(selected_week) > 0:
                selected_date = selected_week[
                    0
                ]  # Prendre la première date si c'est un tuple
            else:
                selected_date = (
                    datetime.now().date()
                )  # Fallback sur aujourd'hui si tuple vide
        else:
            selected_date = selected_week  # Si c'est une seule date

        # S'assurer que selected_date n'est pas None
        if selected_date is None:
            selected_date = datetime.now().date()

        # Convertir en datetime
        selected_datetime = datetime.combine(selected_date, datetime.min.time())
        st.session_state.selected_date = selected_datetime
        st.session_state.messages[0] = get_system_message(selected_datetime)
        st.divider()
        if st.button("Clear Conversation"):
            st.session_state.messages = [st.session_state.messages[0]]

    # Chat input
    prompt = st.chat_input("Ask me about planning your calendar...")
    if prompt:
        chat_input_handler(prompt)

    # Display chat
    display_chat()

    # Action buttons
    cols = st.columns(2)
    with cols[0]:
        if st.button("📝 Plan my work week", use_container_width=True):
            chat_input_handler("Please help me plan my work week effectively")
    with cols[1]:
        if st.button("🎯 Optimize my schedule", use_container_width=True):
            chat_input_handler("Please help me optimize my current schedule")

    # Events view
    with st.expander("📅 View Calendar Events"):
        display_events()

    # Calendar view
    with st.expander("📅 Calendar View"):
        display_events_calendar()
    # Export calendar
    if st.button("Export to Calendar"):
        response = requests.post(
            f"{BACKEND_URL}/export-ics", json=st.session_state.messages
        )
        if response.status_code == 200:
            st.download_button(
                label="Download Calendar (ICS)",
                data=response.text,
                file_name="schedule.ics",
                mime="text/calendar",
            )


if __name__ == "__main__":
    main()

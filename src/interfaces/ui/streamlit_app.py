import json
from datetime import datetime, timedelta

import requests
import streamlit as st
from streamlit_calendar import calendar

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
                    "functions": get_llm_functions(),
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
    logger.debug(f"Assistant Response: {data}")
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


def set_custom_style():
    st.markdown(
        """
        <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

        /* Apply font */
        html, body, [class*="css"]  {
            font-family: 'Roboto', sans-serif;
        }

        /* Main container */
        .main {
            padding: 1rem;
            background-color: #f9fafb;
        }

        /* Header */
        h1, h2, h3, h4, h5, h6 {
            color: #1f2937;
        }

        /* Chat messages */
        .stChatMessage {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        /* Buttons */
        .stButton button {
            border-radius: 8px;
            border: none;
            background-color: #2563eb;
            color: white;
            padding: 0.6rem 1rem;
            font-weight: 500;
            transition: background-color 0.3s ease, transform 0.2s ease;
        }

        .stButton button:hover {
            background-color: #1d4ed8;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        /* Event cards */
        .event-card {
            background: white;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            border-left: 4px solid #2563eb;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.2s ease;
        }

        .event-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        /* Responsive layout */
        @media (max-width: 768px) {
            .block-container {
                padding: 1rem;
            }
            .stCols {
                flex-direction: column;
            }
        }

        /* Dark mode */
        @media (prefers-color-scheme: dark) {
            body {
                background-color: #111827;
                color: #f9fafb;
            }
            .main {
                background-color: #1f2937;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #f9fafb;
            }
            .stChatMessage {
                background-color: #374151;
                color: #f9fafb;
            }
            .event-card {
                background-color: #374151;
                border-left-color: #3b82f6;
            }
            .stButton button {
                background-color: #3b82f6;
            }
            .stButton button:hover {
                background-color: #2563eb;
            }
        }
        </style>
    """,
        unsafe_allow_html=True,
    )


def display_events() -> None:
    response = requests.get(f"{BACKEND_URL}/events")
    if response.status_code == 200:
        events = response.json()
        if events:
            # Map events to the format expected by streamlit_calendar
            calendar_events = [
                {
                    "title": event["event_name"],
                    "start": event["event_start_date_time"],
                    "end": event["event_end_date_time"],
                    # Include additional fields if necessary
                }
                for event in events
            ]

            # Define calendar options
            calendar_options = {
                "initialView": "timeGridWeek",
                "editable": True,
                "selectable": True,
                "headerToolbar": {
                    "left": "prev,next today",
                    "center": "title",
                    "right": "dayGridMonth,timeGridWeek,timeGridDay",
                },
                "slotMinTime": "06:00:00",
                "slotMaxTime": "22:00:00",
            }

            # Custom CSS for calendar styling
            custom_css = """
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
                    font-size: 1.5rem;
                }
            """

            # Render the calendar
            calendar_component = calendar(
                events=calendar_events, options=calendar_options, custom_css=custom_css
            )
            st.write(calendar_component)
        else:
            st.info("No events to display.")
    else:
        st.error("Failed to fetch events")


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
        page_title="Calendar Planning Assistant",
        page_icon="📅",
        layout="wide",
        initial_sidebar_state="expanded",
        # Removed 'theme' parameter
    )

    set_custom_style()

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = [get_system_message(datetime.now())]
    if "query_status" not in st.session_state:
        st.session_state.query_status = ""
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = datetime.now()

    # Chat input at root level
    prompt = st.chat_input("How can I assist you with your calendar?")
    if prompt:
        with st.spinner("Processing your request..."):
            chat_input_handler(prompt)

    # Layout with columns
    left_col, right_col = st.columns([2, 1], gap="large")

    with left_col:
        st.title("🗓️ Calendar Planning Assistant")

        # Chat interface
        st.markdown("### 💬 Chat")
        display_chat()

    with right_col:
        st.markdown("### 📅 Calendar Events")
        # Quick actions
        col1, col2 = st.columns(2, gap="small")
        with col1:
            if st.button(
                "📝 Plan Week",
                help="Plan your work week efficiently",
                use_container_width=True,
            ):
                with st.spinner("Planning your week..."):
                    chat_input_handler("Please help me plan my work week effectively")
        with col2:
            if st.button(
                "🎯 Optimize Schedule",
                help="Optimize your current schedule",
                use_container_width=True,
            ):
                with st.spinner("Optimizing schedule..."):
                    chat_input_handler("Please help me optimize my current schedule")

        # Calendar view
        display_events()

        # Export button
        if st.button("📤 Export Calendar", use_container_width=True):
            with st.spinner("Preparing calendar export..."):
                response = requests.post(
                    f"{BACKEND_URL}/export-ics", json=st.session_state.messages
                )
                if response.status_code == 200:
                    st.download_button(
                        label="⬇️ Download ICS",
                        data=response.text,
                        file_name="schedule.ics",
                        mime="text/calendar",
                        use_container_width=True,
                    )

    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        selected_week = st.date_input(
            "Week Starting From:", datetime.now().date(), key="date_picker"
        )

        # Improved date input handling
        if isinstance(selected_week, tuple):
            # Handle tuple case (multiple dates selected)
            selected_date = (
                selected_week[0] if len(selected_week) > 0 else datetime.now().date()
            )
        else:
            # Handle single date case
            selected_date = (
                selected_week if selected_week is not None else datetime.now().date()
            )

        # Now selected_date is guaranteed to be a date object
        selected_datetime = datetime.combine(selected_date, datetime.min.time())
        st.session_state.selected_date = selected_datetime
        st.session_state.messages[0] = get_system_message(selected_datetime)

        st.divider()
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = [st.session_state.messages[0]]
            st.experimental_rerun()


if __name__ == "__main__":
    main()

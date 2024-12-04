import json
from datetime import datetime, timedelta

import requests
import streamlit as st
from streamlit_calendar import calendar
import streamlit.components.v1 as components

from src.core.logger import setup_logger

logger = setup_logger(__name__)

BACKEND_URL = "http://localhost:8000"


def get_system_message(selected_date: datetime) -> dict:
    weekday = selected_date.strftime("%A")
    days_until_friday = 4 - selected_date.weekday()
    if days_until_friday < 0:
        days_until_friday = 0
    end_date = selected_date + timedelta(days=days_until_friday)

    split_instruction = (
        """
        - When enabled, always split any event longer than 2 hours into smaller tasks
        - Each task should be between 30 minutes and 2 hours
        - Break down events logically based on their description
        """
        if st.session_state.get("enable_event_splitting", False)
        else ""
    )

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
        - Only schedule within this specific work week period
        {split_instruction}""",
    }


def on_keypress():
    return """
<script>
document.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();  // Empêcher le comportement par défaut
        var form = document.querySelector('form');
        if (form) {
            form.dispatchEvent(new Event('submit'));
        }
    }
});
</script>
"""

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
    elif function_name == "split_event":
        handle_split_event(arguments)

    st.session_state.query_status = "Success"
    st.rerun()


def handle_insert_event(arguments: dict) -> None:
    # Calculate event duration in minutes
    start_time = datetime.fromisoformat(arguments["event_start_date_time"])
    end_time = datetime.fromisoformat(arguments["event_end_date_time"])
    duration = (end_time - start_time).total_seconds() / 60

    # If event splitting is enabled and event is longer than 2 hours
    if st.session_state.get("enable_event_splitting", False) and duration > 120:
        # Create initial event to get its ID
        response = requests.post(f"{BACKEND_URL}/events", json=arguments)
        if response.status_code == 200:
            event = response.json()
            # Ask LLM to split the event
            split_prompt = f"""Please split this event into smaller tasks:
            Event: {arguments['event_name']}
            Description: {arguments.get('event_description', '')}
            Duration: {duration} minutes
            Each task should be between 30 and 120 minutes."""

            st.session_state.messages.append(
                {"role": "system", "content": split_prompt}
            )

            split_response = requests.post(
                f"{BACKEND_URL}/chat",
                json={
                    "messages": st.session_state.messages,
                    "selected_date": st.session_state.selected_date.isoformat(),
                    "functions": [
                        f for f in get_llm_functions() if f["name"] == "split_event"
                    ],
                },
            )

            if split_response.status_code == 200:
                handle_chat_response(split_response.json())
            else:
                st.error("Failed to split event")
    else:
        # Handle normal event creation
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


def handle_split_event(arguments: dict) -> None:
    response = requests.post(f"{BACKEND_URL}/events/split", json=arguments)
    if response.status_code == 200:
        st.success("Event split successfully!")
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "I've split the event into smaller tasks in your calendar.",
            }
        )
    else:
        st.error("Failed to split event")


def display_chat() -> None:
    for message in st.session_state.messages[1:]:  # Skip system message
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def set_custom_style():
    st.markdown(
        """
        <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Apply font */
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
            background-color: #f0f2f5;
        }

        /* Main container */
        .main {
            padding: 2rem;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }

        /* Header */
        h1, h2, h3, h4, h5, h6 {
            color: #111827;
            font-weight: 600;
        }

        /* Chat messages */
        .stChatMessage {
            background-color: #f9fafb;
            border-radius: 16px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        /* Buttons */
        .stButton button {
            border-radius: 8px;
            border: none;
            background-color: #2563eb;
            color: white;
            padding: 0.75rem 1.25rem;
            font-weight: 500;
            transition: background-color 0.3s ease, box-shadow 0.2s ease;
        }

        .stButton button:hover {
            background-color: #1d4ed8;
            box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        }

        /* Event cards */
        .event-card {
            background: #ffffff;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            border-left: 5px solid #2563eb;
            box-shadow: 0 3px 6px rgba(0,0,0,0.05);
            transition: transform 0.2s ease;
        }

        .event-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        }

        /* Responsive layout */
        @media (max-width: 768px) {
            .main {
                padding: 1rem;
            }
            .stContainer {
                padding: 0;
            }
            .stButton button {
                width: 100%;
            }
        }

        /* Dark mode */
        @media (prefers-color-scheme: dark) {
            html, body, [class*="css"]  {
                background-color: #1a202c;
                color: #e2e8f0;
            }
            .main {
                background-color: #2d3748;
            }
            .stChatMessage {
                background-color: #4a5568;
            }
            .event-card {
                background-color: #4a5568;
                border-left-color: #3b82f6;
            }
            .stButton button {
                background-color: #3b82f6;
            }
            .stButton button:hover {
                background-color: #2563eb;
            }
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
            .main {
                padding: 1rem;
            }
            .stButton button {
                width: 100%;
                margin-bottom: 0.5rem;
            }
            .stChatMessage {
                padding: 0.75rem;
                margin: 0.25rem 0;
            }
            .event-card {
                padding: 1rem;
            }
            h1 {
                font-size: 1.5rem;
            }
            h2, h3 {
                font-size: 1.25rem;
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
            # Map events to the format expected by st_fullcalendar
            calendar_events = [
                {
                    "title": event["event_name"],
                    "start": event["event_start_date_time"],
                    "end": event["event_end_date_time"],
                    # Include additional fields if necessary
                }
                for event in events
            ]

            # Define calendar options with initialDate
            calendar_options = {
                "initialView": "timeGridWeek",
                "initialDate": st.session_state.selected_date.strftime("%Y-%m-%d"),
                "editable": True,
                "selectable": True,
                "headerToolbar": {
                    "left": "prev,next today",
                    "center": "title",
                    "right": "dayGridMonth,timeGridWeek,timeGridDay",
                },
                "slotMinTime": "06:00:00",
                "slotMaxTime": "22:00:00",
                # Include any other FullCalendar options you need
            }

            # Render the calendar using st_fullcalendar
            calendar(calendar_events, calendar_options)
        else:
            st.info("No events to display.")
    else:
        st.error("Failed to fetch events")


def get_llm_functions() -> list:
    functions = [
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

    if st.session_state.get("enable_event_splitting", False):
        functions.append(
            {
                "name": "split_event",
                "description": "Split a single event into multiple smaller tasks",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "integer",
                            "description": "ID of the event to split",
                        },
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "task_name": {"type": "string"},
                                    "task_start_date_time": {
                                        "type": "string",
                                        "format": "date-time",
                                        "description": "Start datetime of the task (ISO format)",
                                    },
                                    "task_end_date_time": {
                                        "type": "string",
                                        "format": "date-time",
                                        "description": "End datetime of the task (ISO format)",
                                    },
                                },
                                "required": [
                                    "task_name",
                                    "task_start_date_time",
                                    "task_end_date_time",
                                ],
                            },
                        },
                    },
                    "required": ["event_id", "tasks"],
                },
            }
        )
    return functions


def main():
    st.set_page_config(
        page_title="Calendar Planning Assistant",
        page_icon="📅",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    components.html(on_keypress(), height=0, width=0)

    # Initialize session state variables
    if "enable_event_splitting" not in st.session_state:
        st.session_state.enable_event_splitting = False
    if "messages" not in st.session_state:
        st.session_state.messages = [get_system_message(datetime.now())]
    if "query_status" not in st.session_state:
        st.session_state.query_status = ""
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = datetime.now()
    if "text_input_value" not in st.session_state:
        st.session_state.text_input_value = ""

    set_custom_style()

    # Use a container for the main content
    with st.container():
        st.title("🗓️ Calendar Planning Assistant")
        
        # Display calendar events
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
        

    # Sidebar remains as is
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

        st.session_state.enable_event_splitting = st.checkbox(
            "Enable Event Splitting",
            value=False,
            help="Allow the assistant to split events into multiple smaller tasks",
        )

        st.divider()
        # Chat Section
        st.markdown("### 💬 Chat")
        display_chat()
        
        st.divider()
        with st.form(key='my_form'):
            prompt = st.text_input("How can I assist you with your calendar?", key="sidebar_chat_input")
            submit_button = st.form_submit_button(label='Send', use_container_width=True)

        if submit_button and prompt:
            with st.spinner("Processing your request..."):
                chat_input_handler(prompt)
            st.session_state.sidebar_chat_input = ""

        st.divider()
        if st.button("🗑️ Clear Chat History", use_container_width=True):
                st.session_state.messages = [st.session_state.messages[0]]
                st.rerun()


if __name__ == "__main__":
    main()

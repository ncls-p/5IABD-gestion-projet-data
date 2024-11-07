import json
import logging
import os
import sys
from datetime import datetime

import psycopg2
import requests
import streamlit as st
from dotenv import load_dotenv

# Environment variables
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mysecretpassword")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

LLM_API_URL = os.getenv("LLM_API_URL")
MODEL_ID = os.getenv("MODEL_ID")
LLM_API_KEY = os.getenv("LLM_API_KEY")

headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}

# Set up logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# App configuration
st.set_page_config(
    page_title="Calendar Planning Assistant", page_icon="📅", layout="centered"
)
st.title("🗓️ Calendar Planning Assistant")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "You are a helpful calendar planning assistant...",
        }
    ]
if "query_status" not in st.session_state:
    st.session_state.query_status = ""

# Calendar context sidebar
with st.sidebar:
    st.header("Calendar Context")
    selected_week = st.date_input("Select Week Starting From:", datetime.now())
    working_hours = st.slider("Working Hours per Day:", 4, 12, 8)
    st.divider()
    if st.button("Clear Conversation"):
        st.session_state.messages = [
            st.session_state.messages[0]
        ]  # Keep system message

# Define functions for LLM
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
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# LLM API call function
def call_llm_api(messages):
    if not LLM_API_URL:
        st.session_state.query_status = "Error: LLM API URL is not configured"
        return None

    try:
        payload = {
            "model": MODEL_ID,
            "messages": messages,
            "functions": functions,
            "function_call": "auto",
            "stream": False,
        }

        logger.debug(f"API Request URL: {LLM_API_URL}")
        logger.debug(f"Request Payload: {json.dumps(payload, indent=2)}")

        with st.spinner("Getting response..."):
            response = requests.post(
                LLM_API_URL, headers=headers, json=payload, timeout=300
            )

        if response.status_code != 200:
            st.session_state.query_status = f"Error: {response.text}"
            return None

        data = response.json()
        print(data)
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            message = choice.get("message", {})
            finish_reason = choice.get("finish_reason", "")

            if finish_reason == "function_call":
                # Assistant is requesting a function call
                function_call = message.get("function_call", {})
                function_name = function_call.get("name")
                arguments_str = function_call.get("arguments", "{}")
                arguments = json.loads(arguments_str)
                # Call the function
                function_response = None
                if function_name == "insert_event":
                    function_response = insert_event(**arguments)
                elif function_name == "get_events":
                    function_response = get_events()
                else:
                    st.session_state.query_status = (
                        f"Error: Unknown function {function_name}"
                    )
                    return None
                # Add the function response to the messages
                messages.append(
                    {
                        "role": "function",
                        "name": function_name,
                        "content": json.dumps(function_response),
                    }
                )
                # Call LLM again with updated messages
                return call_llm_api(messages)
            elif finish_reason == "stop":
                # Regular assistant response
                if "content" in message and message["content"]:
                    st.session_state.query_status = "Success ✅"
                    return message.get("content")
                else:
                    st.session_state.query_status = "Error: No content in message"
                    return None
            else:
                st.session_state.query_status = (
                    f"Error: Unexpected finish_reason '{finish_reason}'"
                )
                return None
        else:
            st.session_state.query_status = "Error: Unexpected response format"
            return None

    except requests.exceptions.Timeout:
        st.session_state.query_status = "Error: Request timed out"
        return None
    except Exception as e:
        st.session_state.query_status = f"Error: {str(e)}"
        return None


# Chat input handler
def chat_input_handler(prompt):
    if prompt:
        # Add user message to session state
        st.session_state.messages.append({"role": "user", "content": prompt})
        try:
            response = call_llm_api(st.session_state.messages)
            if response:
                # Add assistant's response to session state
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
                st.session_state.query_status = "Success"
            else:
                st.session_state.query_status = "Failed to get response"
        except Exception as e:
            st.session_state.query_status = f"Error: {str(e)}"


# Display chat history
def display_chat():
    for message in st.session_state.messages[1:]:  # Skip system message
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# Button click handler
def handle_button_click(prompt):
    chat_input_handler(prompt)
    display_chat()  # Display chat history after processing the button click


# Database connection
def create_postgres_connection():
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        port=POSTGRES_PORT,
    )
    return conn


# Create table if not exists
def create_table():
    conn = create_postgres_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS calendar_events (
            id SERIAL PRIMARY KEY,
            event_name VARCHAR(255) NOT NULL,
            event_description TEXT,
            event_start_date_time TIMESTAMP NOT NULL,
            event_end_date_time TIMESTAMP NOT NULL,
            event_location VARCHAR(255)
        )
        """
    )
    conn.commit()
    conn.close()


# Get events from database
def get_events():
    conn = create_postgres_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM calendar_events")
    rows = cur.fetchall()
    conn.close()
    # Convert events to dicts
    events = []
    for row in rows:
        events.append(
            {
                "id": row[0],
                "event_name": row[1],
                "event_description": row[2],
                "event_start_date_time": row[3].isoformat(),
                "event_end_date_time": row[4].isoformat(),
                "event_location": row[5],
            }
        )
    return events


# Get database structure
def get_db_structure():
    conn = create_postgres_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            table_name,
            column_name,
            data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
    """)
    columns = cur.fetchall()
    conn.close()
    return columns


def db_structure_as_string():
    columns = get_db_structure()
    return "\n".join(
        [
            f"{table_name}: {column_name} ({data_type})"
            for table_name, column_name, data_type in columns
        ]
    )


# Insert event into database
def insert_event(
    event_name,
    event_description,
    event_start_date_time,
    event_end_date_time,
    event_location,
):
    conn = create_postgres_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO calendar_events (event_name, event_description, event_start_date_time, event_end_date_time, event_location)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            event_name,
            event_description,
            event_start_date_time,
            event_end_date_time,
            event_location,
        ),
    )
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Event inserted successfully"}


# Display chat input
prompt = st.chat_input("Ask me about planning your calendar...")
if prompt:
    chat_input_handler(prompt)
    display_chat()

# Button section
cols = st.columns(2)
with cols[0]:
    if st.button("📝 Plan my work week", use_container_width=True):
        handle_button_click("Please help me plan my work week effectively")
with cols[1]:
    if st.button("🎯 Optimize my schedule", use_container_width=True):
        handle_button_click("Please help me optimize my current schedule")

with cols[0]:
    if st.button("Show db structure", use_container_width=True):
        handle_button_click("Show me the database structure")

# Expanders for events and database structure
with st.expander("📅 View Calendar Events"):
    create_table()
    events = get_events()
    if events:
        st.table(events)
    else:
        st.write("No events found")

with st.expander("📊 Database Structure"):
    tables = db_structure_as_string()
    st.write(tables)

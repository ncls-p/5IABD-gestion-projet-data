import json
import logging
import os
import sys
from datetime import datetime

import requests
import streamlit as st
from dotenv import load_dotenv

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

# API setup
LLM_API_URL = os.getenv("LLM_API_URL")
MODEL_ID = os.getenv("MODEL_ID")
LLM_API_KEY = os.getenv("LLM_API_KEY")

headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}

# Initialize all required session states
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful calendar planning assistant..."}
    ]
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_query" not in st.session_state:
    st.session_state.selected_query = ""
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


def call_llm_api(messages):
    try:
        payload = {"model": MODEL_ID, "messages": messages, "stream": False}

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
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                st.session_state.query_status = "Success ✅"
                with st.chat_message("assistant"):
                    st.write(message.get("content"))
                return message.get("content")
            else:
                st.session_state.query_status = "Error: Unexpected response format"
                return None

    except requests.exceptions.Timeout:
        st.session_state.query_status = "Error: Request timed out"
        return None
    except Exception as e:
        st.session_state.query_status = f"Error: {str(e)}"
        return None


def get_llm_response(messages):
    response = call_llm_api(messages)
    if response is None:
        logger.error("Failed to get response from API")
        return "Sorry, I couldn't process your request."
    return response


def chat_input_handler(prompt):
    if prompt:
        # Immediately display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Update both states
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.selected_query = prompt

        try:
            response = call_llm_api(st.session_state.messages)
            if response:
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.chat_history.append({"role": "assistant", "content": response})
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

# Single display of chat history
display_chat()

# Handle new input
prompt = st.chat_input("Ask me about planning your calendar...")
if prompt:
    chat_input_handler(prompt)


# Remove status display section since we're using chat interface
def handle_button_click(prompt):
    # Only display message once
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Update state once
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    try:
        response = call_llm_api(st.session_state.messages)
        if response:
            # Display response once
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
    except Exception as e:
        logger.error(f"Error: {str(e)}")

# Button section only
cols = st.columns(2)
with cols[0]:
    if st.button("📝 Plan my work week", use_container_width=True):
        handle_button_click("Please help me plan my work week effectively")
with cols[1]:
    if st.button("🎯 Optimize my schedule", use_container_width=True):
        handle_button_click("Please help me optimize my current schedule")


import os
import json
import requests
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
import logging
import sys

# Set up logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# App configuration
st.set_page_config(
    page_title="Calendar Planning Assistant", page_icon="📅", layout="wide"
)
st.title("🗓️ Calendar Planning Assistant")

# API setup
LLM_API_URL = "https://owebui.nclsp.com/ollama/v1/chat/completions"
MODEL_ID = "qwen2.5:7b"
LLM_API_KEY = os.getenv("LLM_API_KEY")

headers = {
    "Authorization": f"Bearer {LLM_API_KEY}",
    "Content-Type": "application/json"
}

def call_llm_api(messages):
    try:
        payload = {
            "model": MODEL_ID,
            "messages": messages,
            "stream": False
        }

        logger.debug(f"API Request URL: {LLM_API_URL}")
        logger.debug(f"Request Payload: {json.dumps(payload, indent=2)}")

        with st.spinner('Getting response...'):
            response = requests.post(
                LLM_API_URL,
                headers=headers,
                json=payload,
                timeout=300
            )

            if response.status_code != 200:
                logger.error(f"API Error Status: {response.status_code}")
                logger.error(f"API Error Response: {response.text}")
                st.error(f"API Error: {response.text}")
                return None

            data = response.json()
            logger.debug(f"API Response: {json.dumps(data, indent=2)}")

            if 'choices' in data and len(data['choices']) > 0:
                message = data['choices'][0].get('message', {})
                with st.chat_message("assistant"):
                    st.write(message.get('content'))
                return message.get('content')
            else:
                error_msg = "Unexpected response format"
                logger.error(f"{error_msg}: {data}")
                st.error(error_msg)
                return None

    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 5 minutes"
        logger.error(error_msg)
        st.error(error_msg)
        return None
    except Exception as e:
        logger.error(f"Exception in API call: {str(e)}")
        st.error(f"Error: {str(e)}")
        return None

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": """You are a helpful calendar planning assistant. Help users organize their weekly schedule.
            Provide specific time slots and structured suggestions. Always maintain a professional tone.""",
        }
    ]

if 'query_status' not in st.session_state:
    st.session_state.query_status = ""
if 'selected_query' not in st.session_state:
    st.session_state.selected_query = ""

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


def get_llm_response(messages):
    response = call_llm_api(messages)
    if response is None:
        logger.error("Failed to get response from API")
        return "Sorry, I couldn't process your request."
    return response


# Display chat history
def display_chat_history():
    for message in st.session_state.messages[1:]:  # Skip system message
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# Main chat interface
display_chat_history()

# Chat input
prompt = st.chat_input("Ask me about planning your calendar...")
if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get assistant response
    with st.chat_message("assistant"):
        context = f"\nContext: Week starting from {selected_week}, {working_hours} working hours per day."
        full_prompt = prompt + context

        with st.spinner("Thinking..."):
            response = get_llm_response(st.session_state.messages)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

def handle_button_click(prompt):
    logger.debug(f"Button clicked with prompt: {prompt}")
    st.session_state.selected_query = prompt
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        response = get_llm_response(st.session_state.messages)
        logger.debug(f"Response received: {response}")
        if response:
            st.session_state.messages.append({"role": "assistant", "content": response})
    except Exception as e:
        logger.error(f"Error in handle_button_click: {str(e)}")

# Update button section without status display
st.markdown("---")
st.caption("Suggested prompts:")
cols = st.columns(2)
with cols[0]:
    if st.button("📝 Plan my work week", use_container_width=True):
        handle_button_click("Please help me plan my work week effectively")
with cols[1]:
    if st.button("🎯 Optimize my schedule", use_container_width=True):
        handle_button_click("Please help me optimize my current schedule")

# Display query statusst.session_state.selected_query:
    st.markdown("---")
    st.write("**Selected Query:**", st.session_state.selected_query)
    st.write("**Status:**", st.session_state.query_status)

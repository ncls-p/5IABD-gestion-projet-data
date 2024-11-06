import os
import json
import requests
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# App configuration
st.set_page_config(
    page_title="Calendar Planning Assistant", page_icon="📅", layout="wide"
)
st.title("🗓️ Calendar Planning Assistant")

# API setup
LLM_API_URL = "https://owebui.nclsp.com/openai"
LLM_API_KEY = os.getenv("LLM_API_KEY")

headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": """You are a helpful calendar planning assistant. Help users organize their weekly schedule.
            Provide specific time slots and structured suggestions. Always maintain a professional tone.""",
        }
    ]

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
    try:
        response = requests.post(
            f"{LLM_API_URL}/chat/completions",
            headers=headers,
            json={
                "model": "qwen2.5-7b",
                "messages": messages,
                "temperature": 0.7,
            },
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"


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

# Add helpful prompt suggestions
st.markdown("---")
st.caption("Suggested prompts:")
cols = st.columns(2)
with cols[0]:
    st.button("📝 Plan my work week", use_container_width=True)
with cols[1]:
    st.button("🎯 Optimize my schedule", use_container_width=True)

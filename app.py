import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Page Configuration
st.set_page_config(
    page_title='Your Custom Gemini Assistant',
    page_icon='🤖',
    layout="wide"
)

# Initialize Session State Variables
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "chats" not in st.session_state:
    st.session_state.chats = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.5
if "system_role" not in st.session_state:
    st.session_state.system_role = "You are a helpful AI assistant."

# --- AUTHENTICATION SCREEN ---
if not st.session_state.api_key:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center;'>Your Custom Gemini Assistant</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #9CA3AF;'>Enter your Google Gemini API key to start chatting.</p>", unsafe_allow_html=True)
        
        api_input = st.text_input("Google API Key", type="password", placeholder="AIzaSy...", label_visibility="collapsed")
        
        if st.button("Continue ➔", use_container_width=True):
            if api_input.strip():
                st.session_state.api_key = api_input.strip()
                if not st.session_state.chats:
                    initial_chat = {"id": 1, "title": "New Chat", "messages": []}
                    st.session_state.chats.append(initial_chat)
                    st.session_state.current_chat_id = 1
                st.rerun()
            else:
                st.error("Please enter a valid API key.")
                
        st.markdown("<br><p style='text-align: center; font-size: 12px; color: #6B7280;'>🔒 Your key is kept only in this browser session and never stored. Get one at <a href='https://aistudio.google.com/' target='_blank'>Google AI Studio</a>.</p>", unsafe_allow_html=True)
    st.stop()

# Helper function to get current chat messages
def get_current_messages():
    for chat in st.session_state.chats:
        if chat["id"] == st.session_state.current_chat_id:
            return chat["messages"]
    return []

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    if st.button("➕ New chat", use_container_width=True):
        new_id = len(st.session_state.chats) + 1
        st.session_state.chats.append({"id": new_id, "title": "New Chat", "messages": []})
        st.session_state.current_chat_id = new_id
        st.rerun()

    st.markdown("### CHATS")
    if not st.session_state.chats:
        st.markdown("<p style='color: #6B7280; font-size: 14px;'>No conversations yet.</p>", unsafe_allow_html=True)
    else:
        for chat in st.session_state.chats:
            if st.button(chat["title"][:25] + ("..." if len(chat["title"]) > 25 else ""), key=f"chat_btn_{chat['id']}", use_container_width=True):
                st.session_state.current_chat_id = chat["id"]
                st.rerun()

    st.markdown("---")
    st.markdown("### SETTINGS")
    
    with st.expander("⚙️ Model & behavior"):
        st.session_state.temperature = st.slider("Temperature", 0.0, 1.0, st.session_state.temperature, 0.05)
        st.session_state.system_role = st.text_area("System role", value=st.session_state.system_role)

    st.markdown("---")
    st.markdown("### ACCOUNT")
    masked_key = f"Key: {st.session_state.api_key[:6]}...{st.session_state.api_key[-4:]}" if len(st.session_state.api_key) > 10 else "Key: Configured"
    st.text(masked_key)
    
    if st.button("➔ Change API key", use_container_width=True):
        st.session_state.api_key = ""
        st.rerun()

# Initialize Chat Model
chat_model = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash", 
    temperature=st.session_state.temperature,
    google_api_key=st.session_state.api_key
)

current_messages = get_current_messages()

# --- WELCOME SCREEN OR CHAT HISTORY ---
if len(current_messages) == 0:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>How can I help you today?</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9CA3AF;'>Ask anything, or pick a suggestion below to get started.</p><br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    suggestions = [
        ("💡 Explain a concept", "Explain how large language models work in simple terms."),
        ("✍️ Write something", "Write a professional email asking for a project deadline extension."),
        ("🛠️ Help me code", "Write a Python function that checks whether a string is a palindrome."),
        ("✈️ Plan a trip", "Plan a 3-day itinerary for a first-time visit to Istanbul.")
    ]
    
    prompt_to_send = None
    for i, (title, text) in enumerate(suggestions):
        target_col = col1 if i % 2 == 0 else col2
        with target_col:
            if st.button(f"**{title}**\n\n{text}", key=f"sug_{i}", use_container_width=True):
                prompt_to_send = text

    if prompt_to_send:
        active_chat = next((c for c in st.session_state.chats if c["id"] == st.session_state.current_chat_id), None)
        if active_chat:
            active_chat["title"] = prompt_to_send[:35]
            active_chat["messages"].append(HumanMessage(content=prompt_to_send))
            
            with st.spinner("Working on your request ..."):
                payload = [SystemMessage(content=st.session_state.system_role)] + active_chat["messages"]
                response = chat_model.invoke(payload)
                
                response_content = response.content
                if isinstance(response_content, list):
                    response_content = "".join(
                        item.get("text", "") if isinstance(item, dict) else str(getattr(item, "text", item))
                        for item in response_content
                    )
                active_chat["messages"].append(AIMessage(content=response_content))
            st.rerun()

else:
    for message in current_messages:
        if isinstance(message, SystemMessage):
            continue
        role = "user" if isinstance(message, HumanMessage) else "assistant"
        
        content = message.content
        if isinstance(content, list):
            content = "".join(
                item.get("text", "") if isinstance(item, dict) else str(getattr(item, "text", item))
                for item in content
            )
            
        with st.chat_message(role):
            st.write(content)

# --- CHAT INPUT BOX ---
user_prompt = st.chat_input("Message your assistant...")

if user_prompt:
    active_chat = next((c for c in st.session_state.chats if c["id"] == st.session_state.current_chat_id), None)
    if active_chat:
        if len(active_chat["messages"]) == 0:
            active_chat["title"] = user_prompt[:35]
            
        active_chat["messages"].append(HumanMessage(content=user_prompt))
        
        with st.chat_message("user"):
            st.write(user_prompt)

        with st.spinner("Working on your request ..."):
            payload = [SystemMessage(content=st.session_state.system_role)] + active_chat["messages"]
            response = chat_model.invoke(payload)
            
            response_content = response.content
            if isinstance(response_content, list):
                response_content = "".join(
                    item.get("text", "") if isinstance(item, dict) else str(getattr(item, "text", item))
                    for item in response_content
                )
                
            active_chat["messages"].append(AIMessage(content=response_content))
            with st.chat_message("assistant"):
                st.write(response_content)
        st.rerun()
import streamlit as st
import requests
import json
import os
from datetime import datetime
from typing import Dict, Any
import dotenv

dotenv.load_dotenv()

# API configuration
# For local development, use the following:
API_BASE_URL = API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
# For production/deployment (e.g., on Render), change to your deployed API URL:
# API_BASE_URL = "https://your-deployed-api-url.onrender.com/api/v1"

USER_SESSION_PATH = os.path.join("data", "user_session.json")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "auth_token" not in st.session_state:
    st.session_state["auth_token"] = ""
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "login_status" not in st.session_state:
    st.session_state["login_status"] = False

# Page config
st.set_page_config(
    page_title="ZUS Coffee Chatbot",
    page_icon="☕",
    layout="wide"
)

# Only use the light theme CSS
st.markdown("""
<style>
    .main-header {
        color: #2c3e50;
    }
    .sub-header {
        color: #7f8c8d;
    }
    .stChatMessage {
        background-color: #f0f2f6;
        color: #222;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        color: #222;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
        color: #222;
    }
    .sidebar-content, .stSidebar {
        background-color: #fff;
        color: #222;
    }
    .stButton>button {
        background-color: #f0f2f6;
        color: #222;
    }
    .stTextInput>div>input {
        background-color: #fff;
        color: #222;
    }
    .stMarkdown, .stMarkdown p {
        color: #222;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">☕ ZUS Coffee Chatbot</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Ask me about ZUS Coffee products and outlets!</p>', unsafe_allow_html=True)

# --- Login/Register Form in Sidebar ---
with st.sidebar:
    if st.session_state["login_status"]:
        # Show logout button at the top when logged in
        st.success(f"Logged in as {st.session_state['username']}")
        if st.button("Logout"):
            st.session_state["auth_token"] = ""
            st.session_state["username"] = ""
            st.session_state["login_status"] = False
            st.session_state["show_register"] = False
            if os.path.exists(USER_SESSION_PATH):
                os.remove(USER_SESSION_PATH)
            st.experimental_rerun()
        # --- Copy JWT for curl ---
        st.markdown("---")
        if st.button("Copy JWT for curl"):
            st.session_state["show_jwt_for_curl"] = True
        if st.session_state.get("show_jwt_for_curl", False):
            st.markdown("**Your JWT Token:**")
            st.code(st.session_state["auth_token"], language="none")
            st.markdown("**Sample curl command:**")
            st.code(f"curl -X POST 'http://127.0.0.1:8000/api/v1/chat' \\\n    -H 'Content-Type: application/json' \\\n    -H 'Authorization: Bearer {st.session_state['auth_token']}' \\\n    -d '{{\"prompt\": \"What is the top 3 drinkware products of ZUS Coffee?\"}}'", language="bash")
            if st.button("Hide JWT for curl"):
                st.session_state["show_jwt_for_curl"] = False
    else:
        st.header("🔑 Login")
        if "show_register" not in st.session_state:
            st.session_state["show_register"] = False
        if not st.session_state["show_register"]:
            # Show Login Form
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
            login_error = ""
            if submitted:
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/login",
                        data={"username": username, "password": password},
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state["auth_token"] = data["access_token"]
                        st.session_state["username"] = username
                        st.session_state["login_status"] = True
                        # Save user info to data/user_session.json
                        os.makedirs("data", exist_ok=True)
                        with open(USER_SESSION_PATH, "w", encoding="utf-8") as f:
                            json.dump({
                                "username": username,
                                "token": data["access_token"],
                                "login_time": datetime.now().isoformat()
                            }, f, indent=2)
                        st.success(f"Logged in as {username}")
                        st.experimental_rerun()
                    else:
                        login_error = response.json().get("detail", "Login failed.")
                except Exception as e:
                    login_error = f"Login error: {e}"
            if login_error:
                st.error(login_error)
            if st.button("Register"):
                st.session_state["show_register"] = True
                st.experimental_rerun()
        else:
            # Show Registration Form
            st.header("📝 Register")
            with st.form("register_form"):
                reg_username = st.text_input("New Username")
                reg_password = st.text_input("New Password", type="password")
                reg_submit = st.form_submit_button("Register")
            if reg_submit:
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/register",
                        data={"username": reg_username, "password": reg_password},
                        timeout=10
                    )
                    if response.status_code == 200:
                        st.success("Registration successful! Please log in.")
                        st.session_state["show_register"] = False
                        st.experimental_rerun()
                    else:
                        reg_msg = response.json().get("detail", "Registration failed.")
                        st.error(reg_msg)
                except Exception as e:
                    st.error(f"Registration error: {e}")
            if st.button("Back to Login"):
                st.session_state["show_register"] = False
                st.experimental_rerun()

# Sidebar for information
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    **Features:**
    - 🛍️ Product search and recommendations
    - 🏪 Outlet locations and details
    - 💬 Natural language conversation
    - 🔍 Semantic search capabilities
    
    **Example queries:**
    - "Show me black tumblers"
    - "Find ZUS outlets in Kuala Lumpur"
    - "What coffee products do you have?"
    - "Where can I find ZUS near me?"
    """)
    
    st.header("🔧 API Status")
    # Check API health
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Error")
    except:
        st.error("❌ API Unavailable")

# --- Helper to get auth headers ---
def get_auth_headers():
    token = st.session_state.get("auth_token", "")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

# API helper functions
def call_products_api(query: str) -> Dict[str, Any]:
    """Call the products API endpoint from the /zus-api backend"""
    headers = get_auth_headers()
    try:
        response = requests.get(f"{API_BASE_URL}/products", params={"query": query}, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

def call_outlets_api(query: str) -> Dict[str, Any]:
    """Call the outlets API endpoint from the /zus-api backend"""
    headers = get_auth_headers()
    try:
        response = requests.get(f"{API_BASE_URL}/outlets", params={"query": query}, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

def call_chat_api(prompt: str) -> Dict[str, Any]:
    """Call the chat API endpoint from the /zus-api backend"""
    headers = get_auth_headers()
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"prompt": prompt},
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

# Chat interface
st.header("💬 Chat")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about ZUS Coffee products or outlets..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Use the chat API endpoint which handles intent classification
                api_response = call_chat_api(prompt)
                
                if "error" in api_response:
                    error_msg = f"API Error: {api_response['error']}"
                    st.error(error_msg)
                    response = error_msg
                else:
                    # Handle different response types
                    if isinstance(api_response, dict):
                        if "summary" in api_response:
                            # Product or outlet response
                            response = api_response["summary"]
                            
                            # Add product details if available
                            if "retrieved_products" in api_response and api_response["retrieved_products"]:
                                response += "\n\n**Products Found:**\n"
                                for i, product in enumerate(api_response["retrieved_products"][:3], 1):
                                    response += f"\n**{i}. {product.get('name', 'Unknown')}**\n"
                                    response += f"   - Category: {product.get('category', 'N/A')}\n"
                                    response += f"   - Price: {product.get('price', 'N/A')}\n"
                                    response += f"   - Color: {product.get('color', 'N/A')}\n"
                                    response += f"   - Image: {product.get('image', 'N/A')}\n"
                                    response += f"   - Score: {product.get('score', 'N/A')}\n"
                                    response += f"   - Description: {product.get('snippet', 'N/A')}\n"
                            # Add outlet details if available
                            if "executed_sql_result" in api_response and api_response["executed_sql_result"]:
                                response += "\n\n**Outlets Found:**\n"
                                for i, outlet in enumerate(api_response["executed_sql_result"][:3], 1):
                                    response += f"\n**{i}. {outlet.get('name', 'Unknown Outlet')}**\n"
                                    response += f"   - Address: {outlet.get('address', 'N/A')}\n"
                                    response += f"   - Phone: {outlet.get('phone_number', outlet.get('contact', 'N/A'))}\n"
                                    response += f"   - Services: {outlet.get('services', 'N/A')}\n"
                                    response += f"   - Place Type: {outlet.get('place_type', 'N/A')}\n"
                                    response += f"   - Opens At: {outlet.get('opens_at', 'N/A')}\n"
                        else:
                            # General chat response
                            response = str(api_response)
                    else:
                        response = str(api_response)
                    
                    st.markdown(response)
                    
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                response = error_msg

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d;'>
    <p>Powered by OpenAI & Pinecone | Built with Streamlit | Connected to FastAPI</p>
</div>
""", unsafe_allow_html=True) 
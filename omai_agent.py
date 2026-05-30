import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
import base64
import json
import os
import time

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="OMAI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# MODERN UI DESIGN
# =========================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #050816, #0B1220);
    color: white;
    font-family: 'Segoe UI';
}
[data-testid="stSidebar"] {
    background: #0A0F1C;
    border-right: 1px solid #1F2937;
}
.main-title {
    font-size: 52px;
    font-weight: 800;
    background: linear-gradient(90deg, #7C3AED, #4F46E5);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.sub-title {
    font-size: 18px;
    color: #9CA3AF;
}
[data-testid="stChatMessage"] {
    background: rgba(17, 24, 39, 0.85);
    border: 1px solid #1F2937;
    border-radius: 18px;
    padding: 12px;
    backdrop-filter: blur(10px);
}
.stChatInput input {
    background: #111827;
    border-radius: 12px;
    border: 1px solid #374151;
    color: white;
}
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-thumb {
    background: #4F46E5;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# MEMORY FILE
# =========================
MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_memory(messages):
    with open(MEMORY_FILE, "w") as f:
        json.dump(messages, f, indent=4)

# =========================
# SESSION INIT
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = load_memory()

# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("# 🤖 OMAI Agent")
st.sidebar.caption("Advanced Offline AI Assistant")
st.sidebar.markdown("---")

if st.sidebar.button("🆕 New Chat"):
    st.session_state.messages = []
    save_memory([])
    st.rerun()

model_name = st.sidebar.selectbox(
    "MODEL",
    ["llama3", "mistral", "phi3", "codellama", "llava"]
)

tool_mode = st.sidebar.radio(
    "TOOL MODE",
    ["Chat", "Code Generator", "Image Analysis", "CSV Analyzer", "Camera AI", "Code Execution", "AI Assistant"]
)

uploaded_image = st.sidebar.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])
csv_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

# =========================
# IMAGE PROCESS
# =========================
image_base64 = None
if uploaded_image:
    img = Image.open(uploaded_image)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    image_base64 = base64.b64encode(buffer.getvalue()).decode()

# =========================
# CSV ANALYZER
# =========================
if csv_file and tool_mode == "CSV Analyzer":
    df = pd.read_csv(csv_file)
    st.subheader("CSV Data")
    st.dataframe(df)

    num_cols = df.select_dtypes(include=["number"]).columns
    if len(num_cols) > 0:
        col = st.selectbox("Select Column", num_cols)
        fig, ax = plt.subplots()
        ax.plot(df[col].values)
        st.pyplot(fig)

# =========================
# AI FUNCTION
# =========================
def ask_ai(prompt, image_data=None):
    system_prompt = f"""
You are OMAI Agent.
Mode: {tool_mode}
Behave like ChatGPT.
"""
    payload = {
        "model": model_name,
        "prompt": system_prompt + "\nUser: " + prompt,
        "stream": False,
        "options": {"temperature": 0.5, "num_predict": 1200}
    }
    if image_data:
        payload["images"] = [image_data]

    try:
        res = requests.post("http://127.0.0.1:11434/api/generate", json=payload, timeout=120)
        return res.json().get("response", "No response")
    except Exception as e:
        return f"Error: {str(e)}"

# =========================
# HEADER
# =========================
st.markdown('<div class="main-title">OMAI Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Offline AI Assistant</div>', unsafe_allow_html=True)
st.markdown("---")

# =========================
# CHAT HISTORY
# =========================
for msg in st.session_state.messages:
    role = msg.get("role", "assistant")
    with st.chat_message(role, avatar="🤖" if role == "assistant" else "🧑"):
        if msg.get("type") == "code":
            st.code(msg.get("content", ""), language="python")
        else:
            st.markdown(msg.get("content", ""))

# =========================
# TOOL MODES
# =========================
if tool_mode == "Camera AI":
    st.subheader("📷 Camera AI (Demo)")
    st.image("https://picsum.photos/400/250", caption="Sample Camera Feed")
    st.info("Here you can integrate live camera feed or object detection.")

elif tool_mode == "Code Execution":
    st.subheader("▶️ Code Execution")

    code = st.text_area(
        "Write Python code here:",
        height=300
    )

    if st.button("Run Code"):

        import io
        import contextlib

        output = io.StringIO()

        try:
            with contextlib.redirect_stdout(output):
                exec(code)

            result = output.getvalue()

            if result.strip():
                st.subheader("Output")
                st.code(result)
            else:
                st.success("Code executed successfully!")

        except Exception as e:
            st.error(f"Error: {e}")

# =========================
# USER INPUT
# =========================
user_prompt = st.chat_input("Ask anything...")
if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt, "type": "text"})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = ask_ai(user_prompt, image_base64)
            placeholder = st.empty()
            typed = ""
            for ch in response:
                typed += ch
                placeholder.markdown(typed)
                time.sleep(0.001)

            if any(k in response for k in ["def ", "class ", "import "]):
                st.code(response, language="python")
                msg_type = "code"
            else:
                st.markdown(response)
                msg_type = "text"

    st.session_state.messages.append({"role": "assistant", "content": response, "type": msg_type})
    save_memory(st.session_state.messages)

# =========================
# DOWNLOAD CHAT
# =========================
st.sidebar.download_button(
    "⬇️ Download Chat",
    json.dumps(st.session_state.messages, indent=4),
    file_name="chat_history.json",
    mime="application/json"
)

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("Powered by Ollama + Streamlit + OMAI Agent")

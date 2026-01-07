import streamlit as st
import google.generativeai as genai
import ollama
import openai
from PIL import Image
import requests
import re
import base64
import io

OPENWEATHER_API_KEY = ""

st.set_page_config(
    page_title="Chatbot",
    page_icon="🤖",
    layout="centered"
)

st.markdown("""
<style>
    .stApp {
        font-family: 'Helvetica Neue', sans-serif;
    }
    .stChatInput {
        border-radius: 20px;
    }
    h1 {
        background: -webkit-linear-gradient(45deg, #00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        padding-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

def supports_vision(model_name, provider):
    if provider == "Gemini":
        return "gemini" in model_name and ("1.5" in model_name or "vision" in model_name)
    elif provider == "OpenAI":
        return "gpt-4" in model_name or "vision" in model_name
    elif provider == "Ollama":
        vision_keywords = ["llava", "vision", "moondream", "minicpm", "yi-vision", "phi-3-vision"]
        if any(k in model_name.lower() for k in vision_keywords):
            return True
        try:
            info = ollama.show(model_name)
            if "clip" in info.get("details", {}).get("families", []):
                return True
        except:
            return False
    return False

def get_weather(city):
    if OPENWEATHER_API_KEY == "YOUR_KEY_HERE":
        return "Error: OpenWeather API Key is not set in the code."

    try:
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"}
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if response.status_code == 200:
            weather_desc = data['weather'][0]['description']
            temp = data['main']['temp']
            return f"Current weather in {city}: {weather_desc}, Temperature: {temp}°C."
        else:
            return f"Error fetching weather: {data.get('message', 'Unknown error')}"
    except Exception as e:
        return f"Error connecting to weather service: {str(e)}"

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def get_openai_response(messages, api_key, model_name):
    client = openai.OpenAI(api_key=api_key)
    formatted_messages = []
    
    for msg in messages:
        if "image_bytes" in msg and msg["role"] == "user":
            base64_image = encode_image(msg["image_bytes"])
            formatted_messages.append({
                "role": msg["role"],
                "content": [
                    {"type": "text", "text": msg["content"]},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            })
        else:
            formatted_messages.append({"role": msg["role"], "content": msg["content"]})

    stream = client.chat.completions.create(
        model=model_name,
        messages=formatted_messages,
        stream=True,
    )
    return stream

def get_gemini_response(messages, api_key, model_name):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    gemini_history = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        parts = [msg["content"]]
        if "image" in msg:
            parts.append(msg["image"])
        gemini_history.append({"role": role, "parts": parts})
    
    chat = model.start_chat(history=gemini_history[:-1])
    
    last_msg = messages[-1]
    last_content = [last_msg["content"]]
    if "image" in last_msg:
        last_content.append(last_msg["image"])

    response = chat.send_message(last_content, stream=True)
    return response

def get_ollama_response(messages, model_name, is_vision_capable):
    ollama_messages = []
    for msg in messages:
        message_data = {"role": msg["role"], "content": msg["content"]}
        if "image_bytes" in msg and is_vision_capable:
            message_data["images"] = [msg["image_bytes"]]
        ollama_messages.append(message_data)

    stream = ollama.chat(
        model=model_name,
        messages=ollama_messages,
        stream=True,
    )
    return stream

def get_ollama_models():
    try:
        models_info = ollama.list()
        return [m['model'] for m in models_info['models']]
    except Exception:
        return []

with st.sidebar:
    st.title("Configuration")
    
    selected_provider = st.radio(
        "Select AI Provider:",
        ("Gemini", "OpenAI (GPT-4o Mini)", "Ollama (Local)"),
        index=0
    )
    
    st.divider()
    
    api_key = ""
    current_model_name = ""
    is_vision_model = False
    
    if selected_provider == "Gemini":
        api_key = st.text_input("Gemini API Key", type="password")
        current_model_name = "gemini-1.5-flash"
        st.caption(f"Model: `{current_model_name}`")
        if supports_vision(current_model_name, "Gemini"):
            is_vision_model = True
            st.success("✅ Vision Ready")
        else:
            st.warning("🚫 Text Only Model")

    elif selected_provider == "OpenAI (GPT-4o Mini)":
        api_key = st.text_input("OpenAI API Key", type="password")
        current_model_name = "gpt-4o-mini"
        st.caption(f"Model: `{current_model_name}`")
        if supports_vision(current_model_name, "OpenAI"):
            is_vision_model = True
            st.success("✅ Vision Ready")
        else:
            st.warning("🚫 Text Only Model")
        
    elif selected_provider == "Ollama (Local)":
        available_models = get_ollama_models()
        if available_models:
            current_model_name = st.selectbox("Select Local Model:", available_models, index=0)
            if supports_vision(current_model_name, "Ollama"):
                is_vision_model = True
                st.success(f"✅ Vision Ready")
            else:
                is_vision_model = False
                st.warning(f"🚫 Text Only Model")
        else:
            st.error("No Ollama models found.")
            st.stop()
            
    st.divider()
    
    uploaded_file = st.file_uploader("Upload an image (optional)", type=["jpg", "png"])
    image_data = Image.open(uploaded_file) if uploaded_file else None
    image_bytes = uploaded_file.getvalue() if uploaded_file else None
    
    if image_data: 
        st.image(image_data, caption="Uploaded", use_container_width=True)
        if not is_vision_model:
            st.error("Selected model cannot see images. The image will be ignored.")

st.title("Chatbot")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message: st.image(message["image"], width=250)
        st.markdown(message["content"])

if prompt := st.chat_input("What is on your mind?"):
    
    weather_info = ""
    if "weather" in prompt.lower() and "in" in prompt.lower():
        match = re.search(r"weather in ([\w\s]+)", prompt, re.IGNORECASE)
        if match:
            city = match.group(1).strip()
            with st.spinner(f"Checking weather for {city}..."):
                weather_info = get_weather(city)

    user_msg = {"role": "user", "content": prompt}
    if image_data:
        user_msg["image"] = image_data
        user_msg["image_bytes"] = image_bytes
    
    st.session_state.messages.append(user_msg)
    
    with st.chat_message("user"):
        if image_data: st.image(image_data, width=250)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        messages_to_send = [msg.copy() for msg in st.session_state.messages]
        
        if weather_info:
            original_content = messages_to_send[-1]["content"]
            system_instruction = f"""
            [SYSTEM DATA]: {weather_info}
            [INSTRUCTION]: The user has asked for the weather. I have provided the raw data above. 
            Please summarize this data for the user in a natural, conversational way. 
            Do not just repeat the data; interpret it (e.g., 'It's quite cold' or 'Expect rain').
            """
            messages_to_send[-1]["content"] = f"{original_content}\n{system_instruction}"

        try:
            if selected_provider == "Gemini":
                if not api_key: st.error("Gemini Key missing."); st.stop()
                chunks = get_gemini_response(messages_to_send, api_key, current_model_name)
                for chunk in chunks:
                    full_response += chunk.text
                    response_placeholder.markdown(full_response + "▌")
            
            elif selected_provider == "OpenAI (GPT-4o Mini)":
                if not api_key: st.error("OpenAI Key missing."); st.stop()
                stream = get_openai_response(messages_to_send, api_key, current_model_name)
                for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_response += content
                        response_placeholder.markdown(full_response + "▌")
            
            elif selected_provider == "Ollama (Local)":
                stream = get_ollama_response(messages_to_send, current_model_name, is_vision_model)
                for chunk in stream:
                    content = chunk['message']['content']
                    full_response += content
                    response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Error: {str(e)}")
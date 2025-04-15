import streamlit as st
import openai
import requests
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import io
import pandas as pd
import base64
import os
from deep_translator import GoogleTranslator  
from fpdf import FPDF
import speech_recognition as sr
from gtts import gTTS
import folium
from streamlit_folium import folium_static  
try:
    import httpx
    if hasattr(httpx, 'BaseTransport'):
        print("httpx is compatible.")
    else:
        print("httpx is not compatible. Downgrading...")
        os.system("pip install 'httpx<1.0.0'")
except ImportError:
    os.system("pip install httpx")


nexus_api_key = "sk-QjjMoRwKPjHXTEzvcum3eA"
nexus_api_url = "https://api.nexus.navigatelabsai.com"

client = openai.OpenAI(
    api_key=nexus_api_key,
    base_url=nexus_api_url
)

weather_api_key = "035b51b6cb61492a929235104253001"


def get_weather_data(city, api_key):
    try:
        
        weather_url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"
        weather_response = requests.get(weather_url)
        weather_response.raise_for_status()  
        return weather_response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch weather data: {e}")
        return None


def get_weather_forecast(city, api_key, days=7):
    try:
        
        forecast_url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={city}&days={days}"
        forecast_response = requests.get(forecast_url)
        forecast_response.raise_for_status()  #
        return forecast_response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch weather forecast data: {e}")
        return None


st.set_page_config(page_title="AI-Powered Disaster Management System", page_icon="🚨", layout="wide")
st.markdown("""
    <style>
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 24px;
        font-size: 16px;
    }
    .stTextInput input {
        border-radius: 5px;
        padding: 10px;
    }
    .stMarkdown h1 {
        color: #2E86C1;
    }
    .stMarkdown h2 {
        color: #148F77;
    }
    .uploaded-image {
        border: 2px solid #4CAF50;
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = []
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def authenticate(username, password):

    return username == "admin" and password == "password"


if not st.session_state.authenticated:
    st.title("🚨 RescueX - Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password.")
    st.stop()


st.title("🚨 RescueX")
st.markdown("""
    Welcome to the **AI-Powered Disaster Management System**! This tool helps emergency responders assess damage, generate reports, and predict future risks using drone data and AI.
    """)


with st.sidebar:
    st.header("📚 Disaster Management Resources")
    st.markdown("""
        - [FEMA Disaster Response Guidelines](https://www.fema.gov/)
        - [Red Cross Disaster Relief](https://www.redcross.org/)
        - [UN Disaster Risk Reduction](https://www.undrr.org/)
        """)

#
st.header("🛠️ Damage Assessment")
st.markdown("Upload drone-captured images or describe the disaster scenario to assess damage and generate a report.")


disaster_description = st.text_input("Describe the disaster scenario (e.g., flooded area, collapsed buildings):")
uploaded_files = st.file_uploader("Or upload drone-captured images:", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    st.session_state.uploaded_images = uploaded_files

if st.session_state.uploaded_images:
    st.subheader("📸 Uploaded Images")
    for uploaded_file in st.session_state.uploaded_images:
        image = Image.open(uploaded_file)
        st.image(image, caption=uploaded_file.name, use_column_width=True, output_format="JPEG", width=300)


if st.button("Generate Rescue Plan"):
    if disaster_description or st.session_state.uploaded_images:
        try:
            
            if disaster_description:
                prompt = f"A drone has captured data about a disaster. The scenario is described as: {disaster_description}. Generate a detailed rescue plan, including the number of rescue teams needed, estimated number of affected people, required food, medicine, and other supplies, and recommended actions."
            else:
                prompt = "A drone has captured images of a disaster-affected area. Generate a detailed rescue plan, including the number of rescue teams needed, estimated number of affected people, required food, medicine, and other supplies, and recommended actions."

            if st.session_state.uploaded_images:
                image_descriptions = []
                for uploaded_file in st.session_state.uploaded_images:
                    image = Image.open(uploaded_file)
                    buffered = io.BytesIO()
                    image.save(buffered, format="JPEG")
                    image_descriptions.append(f"Image {uploaded_file.name} shows a disaster-affected area.")
                prompt += " " + " ".join(image_descriptions)

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a disaster management assistant. Analyze the disaster scenario and generate a detailed rescue plan."},
                    {"role": "user", "content": prompt}
                ]
            )
            rescue_plan = response.choices[0].message.content

            st.success("**Rescue Plan:**")
            st.write(rescue_plan)

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Impact Assessment Report", ln=True, align="C")
            pdf.multi_cell(0, 10, txt=rescue_plan)
            pdf_output = pdf.output(dest="S").encode("latin1")
            st.download_button("Download Report as PDF", pdf_output, file_name="impact_assessment_report.pdf")

        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please describe the disaster scenario or upload images.")


st.header("🎤 Voice and Speech Recognition")
st.markdown("Use voice commands to interact with the system.")


recognizer = sr.Recognizer()
with sr.Microphone() as source:
    st.write("Speak something...")
    audio = recognizer.listen(source)
    try:
        voice_input = recognizer.recognize_google(audio)
        st.write(f"You said: {voice_input}")
    except sr.UnknownValueError:
        st.error("Could not understand audio.")
    except sr.RequestError:
        st.error("Could not request results from Google Speech Recognition.")


if st.button("Convert Text to Speech"):
    text = st.text_input("Enter text to convert to speech:")
    if text:
        tts = gTTS(text)
        tts.save("output.mp3")
        st.audio("output.mp3")


st.header("🔮 Predictive Insights")
st.markdown("Enter details about the disaster to predict future risks and recommend mitigation strategies.")


city = st.text_input("Enter the city:")
disaster_type = st.selectbox("Select the type of disaster:", ["Flood", "Earthquake", "Wildfire", "Hurricane", "Other"])
timeframe = st.slider("Select the timeframe for prediction (in hours):", 1, 72, 24)

if st.button("Generate Predictive Insights"):
    if city and disaster_type:
        try:
            
            weather_data = get_weather_data(city, weather_api_key)
            forecast_data = get_weather_forecast(city, weather_api_key)

            if weather_data and forecast_data:
                
                temperature = weather_data["current"]["temp_c"]
                humidity = weather_data["current"]["humidity"]
                weather_condition = weather_data["current"]["condition"]["text"]
                wind_speed = weather_data["current"]["wind_kph"]

                
                st.subheader("🌤️ Live Weather Data")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Temperature", f"{temperature} °C")
                col2.metric("Humidity", f"{humidity} %")
                col3.metric("Weather Condition", weather_condition)
                col4.metric("Wind Speed", f"{wind_speed} km/h")

                
                st.subheader("📊 Weather Graphs")

                
                forecast_days = forecast_data["forecast"]["forecastday"]
                dates = [day["date"] for day in forecast_days]
                temps = [day["day"]["avgtemp_c"] for day in forecast_days]
                fig_temp = go.Figure(data=go.Scatter(x=dates, y=temps, mode='lines+markers', name='Temperature (°C)'))
                fig_temp.update_layout(title="Temperature Trend Over Next 7 Days", xaxis_title="Date", yaxis_title="Temperature (°C)")
                st.plotly_chart(fig_temp)

                
                humidity_data = [day["day"]["avghumidity"] for day in forecast_days]
                wind_data = [day["day"]["maxwind_kph"] for day in forecast_days]
                fig_humidity_wind = go.Figure(data=[
                    go.Bar(name='Humidity (%)', x=dates, y=humidity_data),
                    go.Bar(name='Wind Speed (km/h)', x=dates, y=wind_data)
                ])
                fig_humidity_wind.update_layout(title="Humidity and Wind Speed Over Next 7 Days", xaxis_title="Date", yaxis_title="Value", barmode='group')
                st.plotly_chart(fig_humidity_wind)

                
                st.subheader("🗺️ Rescue Map")
                lat = weather_data["location"]["lat"]
                lon = weather_data["location"]["lon"]

                
                rescue_map = folium.Map(location=[lat, lon], zoom_start=10)

                
                folium.Marker(
                    location=[lat, lon],
                    popup="Disaster Zone",
                    icon=folium.Icon(color="red", icon="exclamation-triangle")
                ).add_to(rescue_map)

                folium.Marker(
                    location=[lat + 0.1, lon + 0.1],
                    popup="Rescue Center",
                    icon=folium.Icon(color="green", icon="medkit")
                ).add_to(rescue_map)

                
                folium_static(rescue_map)

                
                prompt = f"A {disaster_type} has occurred in {city}. The current weather conditions are: Temperature {temperature} °C, Humidity {humidity}%, Weather Condition {weather_condition}, Wind Speed {wind_speed} km/h. Predict the potential risks and impacts over the next {timeframe} hours. Provide recommendations for mitigation and response."
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a disaster prediction assistant. Analyze the disaster scenario and provide predictive insights and recommendations."},
                        {"role": "user", "content": prompt}
                    ]
                )
                insights = response.choices[0].message.content

                
                st.success("**Predictive Insights:**")
                st.write(insights)
            else:
                st.error("Failed to fetch weather data. Please check the location and API key.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter the city and select the disaster type.")


st.header("🤖 Chatbot Assistant")
st.markdown("Ask questions about disaster management, response strategies, or recovery plans:")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages
        )
        bot_response = response.choices[0].message.content

        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        with st.chat_message("assistant"):
            st.markdown(bot_response)
    except Exception as e:
        st.error(f"An error occurred: {e}")
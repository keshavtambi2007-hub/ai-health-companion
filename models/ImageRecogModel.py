import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# 1. Setup & Configuration (FREE TIER)
st.set_page_config(page_title="Free Food Scanner", page_icon="🍱")
GOOGLE_API_KEY = "AIzaSyCGjtBTQF_akqTDrh3aWDR1m07OPcMpcqM" # Get from aistudio.google.com
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview') # Fastest & Free

# 2. UI Header
st.title("🍱 Hostel Food Scanner (Free Version)")
st.info("Snap a photo to get instant nutrition facts for free.")

# 3. Camera Input
img_file = st.camera_input("Take a photo of your food")

if img_file:
    img = Image.open(img_file)
    st.image(img, caption="Analyzing...", use_container_width=True)
    
    with st.spinner("🤖 Gemini AI is thinking..."):
        try:
            # 4. Prompt for Gemini
            prompt = """
            Analyze this food plate. Identify all items. Estimate portions. 
            Return ONLY a JSON object with this structure:
            {
              "items": [{"name": "item", "weight": "100g", "calories": 100, "protein": 5, "carbs": 20, "fat": 2}],
              "total_calories": 350,
              "health_flags": ["High Carb"],
              "suggestions": ["Add salad"]
            }
            Use Indian hostel mess standards.
            """
            
            # 5. Call Gemini API
            response = model.generate_content([prompt, img])
            
            # Clean the response text (Gemini sometimes adds ```json ... ```)
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            data = json.loads(raw_text)

            # 6. Display Results
            st.success("Scan Complete!")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Calories", f"{data['total_calories']} kcal")
            c2.metric("Protein", f"{sum(i['protein'] for i in data['items'])}g")
            c3.metric("Carbs", f"{sum(i['carbs'] for i in data['items'])}g")
            c4.metric("Fat", f"{sum(i['fat'] for i in data['items'])}g")

            st.write("### 🥗 Breakdown")
            for i in data['items']:
                st.write(f"- {i['name']} ({i['weight']}): {i['calories']} cal")

            if data['health_flags']:
                st.warning(f"⚠️ {', '.join(data['health_flags'])}")
            
            st.info(f"💡 {data['suggestions'][0]}")

        except Exception as e:
            st.error(f"Error: {e}. Check if your API key is correct!")

st.markdown("---")
st.caption("Free Hackathon Version - Powered by Gemini 1.5 Flash")
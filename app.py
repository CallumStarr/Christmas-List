import streamlit as st
import google.generativeai as genai
import json
import urllib.parse

# --- CONFIGURATION ---
# 1. Get your API Key here: https://aistudio.google.com/
# 2. Add your Amazon Affiliate Tag below
AMAZON_TAG = "your-affiliate-tag-20"

# Configure the page
st.set_page_config(page_title="Santa's AI Helper", page_icon="🎄", layout="centered")

# --- CSS STYLING ---
# Streamlit allows custom CSS to make cards look pretty
st.markdown("""
    <style>
    .gift-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #c0392b;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .gift-title {
        font-size: 20px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 5px;
    }
    .gift-reason {
        color: #555;
        font-style: italic;
        margin-bottom: 10px;
    }
    .gift-benefit {
        color: #2980b9;
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("🎄 Santa's AI Helper")
st.write("Enter your child's interests to generate the perfect Christmas list.")

# --- SIDEBAR / INPUTS ---
with st.form("gift_form"):
    interests = st.text_area("Child's Interests", placeholder="e.g. Paw Patrol, muddy puddles, dinosaurs, cooking")
    goals = st.text_input("Parent Goals", placeholder="e.g. Montessori, durable, quiet play, educational")
    age = st.text_input("Age Group", placeholder="e.g. 3 year old toddler")
    submitted = st.form_submit_button("Generate Gift List")

# --- LOGIC ---
if submitted:
    if not interests:
        st.warning("Please enter some interests first!")
    else:
        # 1. Setup Gemini Secret
        # This will look for the key in Streamlit Secrets (cloud) or local secrets.toml
        try:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        except FileNotFoundError:
            st.error("API Key not found. Please set GOOGLE_API_KEY in your secrets.")
            st.stop()

        with st.spinner("✨ Checking with the Elves..."):
            try:
                # 2. The Prompt
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"""
                Act as an expert child development specialist. 
                I need a list of 5 specific toy or gift ideas for a {age}.
                
                The child's interests are: {interests}
                The parent's goals for the gifts are: {goals}

                Strictly return the response in valid JSON format with this structure:
                [
                    {{
                        "gift_name": "Name of the item",
                        "why_it_fits": "Short reason why it fits interests",
                        "developmental_benefit": "Short educational benefit"
                    }}
                ]
                """
                
                response = model.generate_content(prompt)
                
                # Clean and Parse JSON
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                gift_data = json.loads(clean_text)

                # 3. Display Results
                st.subheader(f"🎁 Top Picks for {age}")
                
                for gift in gift_data:
                    # Construct Amazon Affiliate Search Link
                    search_term = urllib.parse.quote(gift['gift_name'])
                    amazon_link = f"https://www.amazon.com/s?k={search_term}&tag={AMAZON_TAG}"

                    # Render Card using Markdown/HTML
                    st.markdown(f"""
                    <div class="gift-card">
                        <div class="gift-title">{gift['gift_name']}</div>
                        <div class="gift-reason">Why: {gift['why_it_fits']}</div>
                        <div class="gift-benefit"><strong>Benefit:</strong> {gift['developmental_benefit']}</div>
                        <br>
                        <a href="{amazon_link}" target="_blank" style="text-decoration:none;">
                            <button style="background-color:#FF9900; color:black; border:none; padding:8px 15px; border-radius:5px; cursor:pointer; font-weight:bold;">
                                View on Amazon 🎁
                            </button>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"The Elves dropped the list! Error: {e}")

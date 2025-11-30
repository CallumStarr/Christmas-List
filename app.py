import streamlit as st
import google.generativeai as genai
import json
import urllib.parse

# --- CONFIGURATION ---
# 1. Get your API Key here: https://aistudio.google.com/
# 2. Add your Amazon Affiliate Tag below (Replace 'your-tag-20')
AMAZON_TAG = "your-tag-20"

# Configure the page settings
st.set_page_config(
    page_title="Santa's AI Helper", 
    page_icon="🎄", 
    layout="centered"
)

# --- CSS STYLING ---
# This makes the results look like nice gift cards instead of plain text
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #2ecc71;
        color: white;
        font-size: 18px;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 24px;
        border: none;
    }
    div.stButton > button:hover {
        background-color: #27ae60;
        color: white;
    }
    .gift-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #c0392b; /* Santa Red */
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        color: #333333;
    }
    .gift-title {
        font-size: 22px;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 8px;
    }
    .gift-reason {
        color: #555;
        font-style: italic;
        margin-bottom: 12px;
        font-size: 15px;
    }
    .gift-benefit {
        color: #2980b9; /* Blue for logic/education */
        font-size: 14px;
        background-color: #f0f8ff;
        padding: 8px;
        border-radius: 6px;
    }
    .amazon-btn {
        display: inline-block;
        background-color: #FF9900; /* Amazon Orange */
        color: black !important;
        padding: 10px 20px;
        border-radius: 6px;
        text-decoration: none;
        font-weight: bold;
        margin-top: 15px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .amazon-btn:hover {
        background-color: #e68a00;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("🎄 Santa's AI Helper")
st.write("Enter the child's interests and your goals to generate the perfect Christmas list.")

# --- SIDEBAR / INPUTS ---
# We use a form so the page doesn't reload on every keystroke
with st.form("gift_form"):
    col1, col2 = st.columns(2)
    with col1:
        age = st.text_input("Age Group", placeholder="e.g. 3 year old toddler")
    with col2:
        budget = st.selectbox("Budget Range", ["Any", "Under $20", "$20 - $50", "$50 - $100", "$100+"])

    interests = st.text_area("Child's Interests", placeholder="e.g. Paw Patrol, muddy puddles, dinosaurs, baking, space")
    goals = st.text_input("Parent Goals", placeholder="e.g. Montessori, durable, quiet play, educational, outdoor activity")
    
    submitted = st.form_submit_button("Generate Gift List")

# --- MAIN LOGIC ---
if submitted:
    if not interests:
        st.warning("Please enter some interests first!")
    else:
        # 1. SETUP API KEY
        # Looks for key in Streamlit Secrets first
        try:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        except (FileNotFoundError, KeyError):
            st.error("API Key not found. Please set GOOGLE_API_KEY in your Streamlit secrets.")
            st.stop()

        with st.spinner("✨ Checking with the Elves..."):
            try:
                # 2. SELECT MODEL (Future-proofed)
                # This alias automatically points to the newest stable Flash model
                model = genai.GenerativeModel('gemini-flash-latest')
                
                # 3. CONSTRUCT PROMPT
                prompt = f"""
                Act as an expert child development specialist and personal shopper. 
                I need a list of 5 specific toy or gift ideas for a {age}.
                
                The child's interests are: {interests}
                The parent's goals for the gifts are: {goals}
                Budget preference: {budget}

                Strictly return the response in valid JSON format with this structure:
                [
                    {{
                        "gift_name": "Name of the item",
                        "why_it_fits": "Short reason why it fits their interests",
                        "developmental_benefit": "Short educational or developmental benefit"
                    }}
                ]
                Do not include markdown formatting (like ```json), just the raw JSON string.
                """
                
                response = model.generate_content(prompt)
                
                # 4. CLEAN AND PARSE JSON
                # Gemini sometimes puts backticks around JSON even if asked not to
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                gift_data = json.loads(clean_text)

                # 5. DISPLAY RESULTS
                st.subheader(f"🎁 Top Picks for {age}")
                
                for gift in gift_data:
                    # Construct Amazon Affiliate Search Link
                    # URL structure: [amazon.com/s?k=](https://amazon.com/s?k=)[search_term]&tag=[affiliate_tag]
                    search_term = urllib.parse.quote(gift['gift_name'])
                    amazon_link = f"[https://www.amazon.com/s?k=](https://www.amazon.com/s?k=){search_term}&tag={AMAZON_TAG}"

                    # Render Card using HTML/CSS defined above
                    st.markdown(f"""
                    <div class="gift-card">
                        <div class="gift-title">{gift['gift_name']}</div>
                        <div class="gift-reason">💡 <em>{gift['why_it_fits']}</em></div>
                        <div class="gift-benefit">🎓 <strong>Development:</strong> {gift['developmental_benefit']}</div>
                        <a href="{amazon_link}" target="_blank" class="amazon-btn">
                            Find on Amazon 🎁
                        </a>
                    </div>
                    """, unsafe_allow_html=True)

            except json.JSONDecodeError:
                st.error("The Elves wrote the list in a weird language! (JSON Error). Please try again.")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

import streamlit as st
import google.generativeai as genai
import json
import urllib.parse

# --- CONFIGURATION ---
# 1. Get your API Key here: https://aistudio.google.com/
# 2. Add your Amazon Affiliate Tag below
AMAZON_TAG = "your-tag-20"

st.set_page_config(page_title="Santa's AI Helper", page_icon="🎄", layout="centered")

# --- CSS STYLING ---
# Since we have no images, we make the cards look extra nice
st.markdown("""
    <style>
    .gift-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        transition: transform 0.2s;
    }
    .gift-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
    }
    .gift-title {
        font-size: 24px;
        font-weight: 800;
        color: #2c3e50;
        margin-bottom: 10px;
    }
    .gift-reason {
        color: #555;
        font-size: 16px;
        line-height: 1.5;
        margin-bottom: 15px;
        border-left: 4px solid #f1c40f;
        padding-left: 10px;
    }
    .gift-benefit {
        color: #2980b9;
        font-size: 15px;
        background-color: #f0f8ff;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 20px;
        border: 1px solid #d6eaf8;
    }
    /* Custom button styling if needed, though we use st.link_button now */
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("🎄 Santa's AI Helper")
st.write("Enter the child's interests to generate a curated gift list.")

# --- INPUT FORM ---
with st.form("gift_form"):
    col1, col2 = st.columns(2)
    with col1:
        age = st.text_input("Age Group", placeholder="e.g. 3 year old")
    with col2:
        budget = st.selectbox("Budget", ["Any", "Under $20", "$20 - $50", "$50+"])

    interests = st.text_area("Child's Interests", placeholder="e.g. Paw Patrol, muddy puddles, dinosaurs")
    goals = st.text_input("Parent Goals", placeholder="e.g. Montessori, durable, quiet play")
    
    submitted = st.form_submit_button("Generate Gift List")

# --- MAIN LOGIC ---
if submitted:
    if not interests:
        st.warning("Please tell Santa what the child likes!")
    else:
        # 1. SETUP API KEY
        try:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        except (FileNotFoundError, KeyError):
            st.error("API Key missing. Please set GOOGLE_API_KEY in Streamlit secrets.")
            st.stop()

        with st.spinner("✨ Checking with the Elves..."):
            try:
                # 2. SELECT MODEL
                # Using latest flash model for speed
                model = genai.GenerativeModel('gemini-flash-latest')
                
                # 3. PROMPT
                # Simplified prompt - we don't need image keywords anymore
                prompt = f"""
                Act as an expert personal shopper for kids. 
                Suggest 5 specific toy names for a {age}.
                Interests: {interests}
                Goals: {goals}
                Budget: {budget}

                Return strictly JSON:
                [
                    {{
                        "gift_name": "Specific Product Name",
                        "why_it_fits": "One sentence on why it fits the interests",
                        "developmental_benefit": "One sentence on the educational benefit"
                    }}
                ]
                """
                
                response = model.generate_content(prompt)
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                gift_data = json.loads(clean_text)

                st.subheader(f"🎁 Top Picks for {age}")

                # 4. DISPLAY LOOP
                for gift in gift_data:
                    # Safely get data
                    name = gift.get('gift_name', 'Mystery Gift')
                    reason = gift.get('why_it_fits', 'Fits your criteria perfectly.')
                    benefit = gift.get('developmental_benefit', 'Great for development.')
                    
                    # Generate Search Link
                    search_query_url = urllib.parse.quote(name)
                    amazon_link = f"https://www.amazon.com/s?k={search_query_url}&tag={AMAZON_TAG}"

                    # Layout
                    with st.container():
                        st.markdown(f"""
                        <div class="gift-card">
                            <div class="gift-title">{name}</div>
                            <div class="gift-reason">💡 {reason}</div>
                            <div class="gift-benefit">🎓 {benefit}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Big, prominent button
                        st.link_button(
                            label=f"👉 Search '{name}' on Amazon", 
                            url=amazon_link,
                            type="primary",
                            use_container_width=True # Makes the button full width
                        )
                        
                        st.write(" ") # Spacer

            except Exception as e:
                st.error(f"The Elves encountered a glitch: {e}")

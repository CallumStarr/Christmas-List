import streamlit as st
import google.generativeai as genai
import json
import urllib.parse

# --- CONFIGURATION ---
# 1. Get your Gemini API Key: https://aistudio.google.com/
# 2. Configure your Amazon Regions and Affiliate Tags below.
AMAZON_CONFIG = {
    "USA (.com)": {
        "domain": ".com", 
        "tag": "your-us-tag-20", 
        "currency": "$"
    },
    "United Kingdom (.co.uk)": {
        "domain": ".co.uk", 
        "tag": "your-uk-tag-21", 
        "currency": "£"
    },
    "Canada (.ca)": {
        "domain": ".ca", 
        "tag": "your-ca-tag-20", 
        "currency": "C$"
    },
    "Australia (.com.au)": {
        "domain": ".com.au", 
        "tag": "your-au-tag-20", 
        "currency": "A$"
    },
    "Germany (.de)": {
        "domain": ".de", 
        "tag": "your-de-tag-21", 
        "currency": "€"
    }
}

st.set_page_config(page_title="Santa's AI Helper", page_icon="🎄", layout="centered")

# --- CSS STYLING ---
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
        margin-bottom: 10px;
        border-left: 4px solid #f1c40f;
        padding-left: 10px;
    }
    .gift-benefit {
        color: #2980b9;
        font-size: 15px;
        background-color: #f0f8ff;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 15px;
        border: 1px solid #d6eaf8;
    }
    .pro-tip {
        background-color: #e8f8f5;
        border: 1px solid #d1f2eb;
        color: #117a65;
        padding: 10px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("🎄 Santa's AI Helper")
st.write("Enter the child's interests to generate a curated gift list.")

# --- INPUT FORM ---
with st.form("gift_form"):
    selected_region = st.selectbox("Select Amazon Region", list(AMAZON_CONFIG.keys()))
    region_data = AMAZON_CONFIG[selected_region]
    currency_symbol = region_data["currency"]
    
    col1, col2 = st.columns(2)
    with col1:
        age = st.text_input("Age Group", placeholder="e.g. 3 year old")
    with col2:
        budget = st.selectbox("Budget", [
            "Any", 
            f"Under {currency_symbol}20", 
            f"{currency_symbol}20 - {currency_symbol}50", 
            f"{currency_symbol}50+"
        ])

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
                model = genai.GenerativeModel('gemini-flash-latest')
                
                # 3. PROMPT (Updated to ask for buying_tip)
                prompt = f"""
                Act as an expert personal shopper for kids. 
                Suggest 5 specific toy names for a {age}.
                Interests: {interests}
                Goals: {goals}
                Budget: {budget}
                Region: {selected_region}

                Return strictly JSON:
                [
                    {{
                        "gift_name": "Specific Product Name",
                        "why_it_fits": "One sentence on why it fits the interests",
                        "developmental_benefit": "One sentence on the educational benefit",
                        "buying_tip": "A short, specific tip to ensure they buy the best version (e.g. 'Look for the Melissa & Doug brand', 'Avoid the plastic version', 'Get the 100-piece set')"
                    }}
                ]
                """
                
                response = model.generate_content(prompt)
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                gift_data = json.loads(clean_text)

                st.subheader(f"🎁 Top Picks for {age}")

                # 4. DISPLAY LOOP
                for gift in gift_data:
                    name = gift.get('gift_name', 'Mystery Gift')
                    reason = gift.get('why_it_fits', 'Fits your criteria perfectly.')
                    benefit = gift.get('developmental_benefit', 'Great for development.')
                    # Get the tip (with a default fallback just in case)
                    tip = gift.get('buying_tip', f"Look for the highest rated version of {name}")
                    
                    # Generate Regional Link
                    domain = region_data["domain"]
                    tag = region_data["tag"]
                    search_query_url = urllib.parse.quote(name)
                    amazon_link = f"https://www.amazon{domain}/s?k={search_query_url}&tag={tag}"

                    # Layout
                    with st.container():
                        st.markdown(f"""
                        <div class="gift-card">
                            <div class="gift-title">{name}</div>
                            <div class="gift-reason">💡 {reason}</div>
                            <div class="gift-benefit">🎓 {benefit}</div>
                            <!-- New Pro Tip Section -->
                            <div class="pro-tip">✨ <strong>Pro Tip:</strong> {tip}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.link_button(
                            label=f"👉 Search '{name}' on Amazon{domain}", 
                            url=amazon_link,
                            type="primary",
                            use_container_width=True
                        )
                        
                        st.write(" ") 

            except Exception as e:
                st.error(f"The Elves encountered a glitch: {e}")

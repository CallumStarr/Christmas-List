import streamlit as st
import google.generativeai as genai
import json
import urllib.parse
import re
import pandas as pd

# --- CONFIGURATION ---
AMAZON_CONFIG = {
    "USA (.com)": {"domain": ".com", "tag": "mcstarrstudio-21", "currency": "$"},
    "United Kingdom (.co.uk)": {"domain": ".co.uk", "tag": "mcstarrstudio-21", "currency": "£"},
    "Canada (.ca)": {"domain": ".ca", "tag": "your-ca-tag-20", "currency": "C$"},
    "Australia (.com.au)": {"domain": ".com.au", "tag": "your-au-tag-20", "currency": "A$"},
    "Germany (.de)": {"domain": ".de", "tag": "your-de-tag-21", "currency": "€"}
}

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Elf-O-Matic | AI Gift Generator", 
    page_icon="🎁", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING ---
st.markdown("""
    <style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #f8f9fa;
    }
    h1 {
        color: #d42426; /* Christmas Red */
        font-family: 'Helvetica', sans-serif;
        font-weight: 800;
    }
    h3 {
        color: #165b33; /* Pine Green */
    }
    
    /* Gift Card Styling */
    .gift-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #d42426;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .gift-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        border-left: 6px solid #165b33;
    }
    .gift-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .gift-title {
        font-size: 20px;
        font-weight: 700;
        color: #333;
    }
    .badge {
        background-color: #e8f5e9;
        color: #1b5e20;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
    .section-title {
        font-size: 14px;
        font-weight: 700;
        color: #555;
        text-transform: uppercase;
        margin-top: 10px;
    }
    .gift-text {
        color: #444;
        font-size: 15px;
        line-height: 1.5;
    }
    
    /* Button Styling */
    div.stButton > button:first-child {
        background-color: #d42426;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 10px 20px;
    }
    div.stButton > button:first-child:hover {
        background-color: #b30002;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE MANAGEMENT ---
if 'results' not in st.session_state:
    st.session_state['results'] = None
if 'generated' not in st.session_state:
    st.session_state['generated'] = False

# --- HELPER FUNCTION: CLEAN JSON ---
def extract_json(text):
    """Robust JSON extraction from LLM response"""
    try:
        # Try finding the first [ and last ]
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        else:
            # Fallback if no brackets found (rare with Gemini JSON mode)
            return json.loads(text)
    except Exception as e:
        return []

# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.title("🎅 Elf-O-Matic 3000")
    st.markdown("Configure your search:")
    
    # 1. API Configuration
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        api_ok = True
    except (FileNotFoundError, KeyError):
        st.error("⚠️ API Key Missing! Set GOOGLE_API_KEY in secrets.")
        api_ok = False

    # 2. User Inputs
    with st.form("gift_form"):
        selected_region = st.selectbox("🌎 Amazon Region", list(AMAZON_CONFIG.keys()))
        region_data = AMAZON_CONFIG[selected_region]
        currency = region_data["currency"]
        
        col1, col2 = st.columns(2)
        with col1:
            age = st.text_input("Age", placeholder="e.g. 7 years old")
        with col2:
            relation = st.text_input("Who is this for?", placeholder="e.g. Son, Niece")

        budget_option = st.select_slider(
            "Budget Per Gift",
            options=["Budget", "Mid-Range", "Premium", "Splurge"],
            value="Mid-Range"
        )
        
        # Translate slider to text for AI
        budget_map = {
            "Budget": f"Under {currency}25",
            "Mid-Range": f"{currency}25 - {currency}60",
            "Premium": f"{currency}60 - {currency}150",
            "Splurge": f"Over {currency}150"
        }
        actual_budget = budget_map[budget_option]
        st.caption(f"Targeting: {actual_budget}")

        interests = st.text_area("🌟 Interests & Obsessions", placeholder="Minecraft, Space, Drawing, Cats...", height=100)
        
        goals = st.text_area("🎯 Gift Goal / Vibe", placeholder="Educational but fun, Main 'Big' Gift, Keepsake...", height=70)

        submitted = st.form_submit_button("Generate Christmas List 🎁")

# --- MAIN CONTENT AREA ---

st.title("🎄 Curated Christmas List Generator")
st.markdown(f"**Current Region:** {selected_region} | **Affiliate Mode:** Active")

if not api_ok:
    st.warning("Please configure your API key to proceed.")
    st.stop()

# --- GENERATION LOGIC ---
if submitted:
    if not interests or not age:
        st.error("⚠️ Please enter at least an Age and Interests.")
    else:
        st.session_state['generated'] = False # Reset
        
        with st.status("✨ The Elves are working...", expanded=True) as status:
            try:
                model = genai.GenerativeModel('gemini-flash-latest') # Use lighter, faster model
                
                status.write("🔍 Analyzing interests...")
                status.write("🎁 Checking Amazon inventory (simulated)...")
                
                prompt = f"""
                You are a world-class personal shopper for Christmas gifts.
                
                CONTEXT:
                - Recipient Age: {age}
                - Relationship: {relation}
                - Interests: {interests}
                - Goal/Vibe: {goals}
                - Budget: {actual_budget}
                - Region: {selected_region}

                TASK:
                Generate a JSON list of exactly 8 highly specific gift ideas.
                
                CRITERIA:
                1. DIVERSITY: Do not suggest 8 of the same type of thing (e.g. don't do 8 Lego sets). Mix categories (Books, Toys, Gear, Decor, etc.) unless the user asked for one specific thing.
                2. SEARCHABILITY: The "search_term" must be easily found on Amazon.
                3. RELEVANCE: Explain exactly why this specific item matches the entered interests.
                
                OUTPUT FORMAT (JSON ARRAY ONLY):
                [
                    {{
                        "category": "Creative / Tech / Outdoor (Pick one)",
                        "gift_name": "Specific Product Name",
                        "amazon_search_term": "Brand Name Product Name Model",
                        "reason": "Why it fits their interests",
                        "impact": "Long term benefit",
                        "buying_tip": "Specific check (e.g. check batteries)"
                    }}
                ]
                """
                
                # Request JSON mode specifically
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                data = extract_json(response.text)
                st.session_state['results'] = data
                st.session_state['generated'] = True
                status.update(label="✅ List Ready!", state="complete", expanded=False)
                
            except Exception as e:
                st.error(f"Elves dropped the list: {e}")

# --- DISPLAY RESULTS ---
if st.session_state['generated'] and st.session_state['results']:
    
    results = st.session_state['results']
    
    # 1. Action Bar (CSV Download)
    df = pd.DataFrame(results)
    csv = df.to_csv(index=False).encode('utf-8')
    
    col_d1, col_d2 = st.columns([8, 2])
    with col_d2:
        st.download_button(
            "📥 Download List",
            data=csv,
            file_name="christmas_list.csv",
            mime="text/csv",
            use_container_width=True
        )

    # 2. Grid Layout for Cards
    for i, gift in enumerate(results):
        # Create valid Amazon Link
        domain = region_data["domain"]
        tag = region_data["tag"]
        raw_term = gift.get('amazon_search_term', gift.get('gift_name'))
        encoded_term = urllib.parse.quote(raw_term.replace('"', ''))
        link = f"https://www.amazon{domain}/s?k={encoded_term}&tag={tag}"
        
        # Display logic
        with st.container():
            st.markdown(f"""
            <div class="gift-card">
                <div class="gift-header">
                    <div class="gift-title">{i+1}. {gift['gift_name']}</div>
                    <span class="badge">{gift.get('category', 'Gift')}</span>
                </div>
                <div class="section-title">Why they'll love it</div>
                <div class="gift-text">{gift['reason']}</div>
                
                <div class="section-title">Lasting Impact</div>
                <div class="gift-text"><i>{gift['impact']}</i></div>
                
                <div style="margin-top:15px; font-size:13px; color:#d68910;">
                    <strong>⚠️ Tip:</strong> {gift['buying_tip']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Use columns to keep the button from stretching too wide
            b_col1, b_col2, b_col3 = st.columns([1, 2, 1])
            with b_col2:
                st.link_button(
                    label=f"👉 Check Price on Amazon{domain}", 
                    url=link,
                    type="primary", 
                    use_container_width=True
                )
            st.write("") # Spacer

elif not submitted:
    # Empty State / Landing info
    st.info("👈 Use the sidebar to tell the Elves about the recipient!")
    st.markdown("""
    ### How it works
    1. **Tell us who it's for:** Age, relationship, and what they love.
    2. **Set your goal:** Are you looking for a 'Main Gift', a 'Stocking Filler', or something educational?
    3. **Get a curated list:** The AI checks for products that fit your description and budget.
    4. **Click to buy:** Direct links to search your local Amazon store.
    """)

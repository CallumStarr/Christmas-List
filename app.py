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
                model = genai.GenerativeModel('gemini-1.5-flash') # Use lighter, faster model
                
                status.write("🔍 Analyzing interests...")
                status.write("🎁 Checking Amazon inventory (simulated)...")
                
                prompt = f"""
                ROLE: You are an expert personal gift shopper, specialising in thoughtful, high-converting Christmas gifts.
                Your task:
                Use the inputs below to recommend exactly 10 specific gift ideas that feel tailored, age-appropriate, and genuinely impressive.
                                
                CONTEXT:
                - Recipient Age: {age}
                - Relationship: {relation}
                - Interests / hobbies: {interests}
                - Gift goals: {goals} (e.g. "funny gift", "something they will love", "something they will cherish forever")
                - Budget: {actual_budget} (total budget for ONE gift, in the currency of the region)
                - Region: {selected_region} (the country/market where the gift will be purchased)

                 TASK:
                Generate a JSON list of exactly 8 highly specific gift ideas.
                
                CRITERIA:
                1. DIVERSITY: Do not suggest 8 of the same type of thing (e.g. don't do 8 Lego sets). Mix categories (Books, Toys, Gear, Decor, etc.) unless the user asked for one specific thing.
                2. SEARCHABILITY: The "search_term" must be easily found on Amazon.
                3. RELEVANCE: Explain exactly why this specific item matches the entered interests.
                               
                GENERAL BEHAVIOUR
                - Think like a human personal shopper who really understands the recipient and the buyer’s intent.
                - Assume these are Christmas gifts: it is fine to subtly reference the festive/holiday context, but core fit and usefulness matter more than being "gimmicky".
                - Strongly prioritise gifts that clearly match BOTH the interests AND the stated goal.
                - Ensure every suggestion is age-appropriate and safe:
                  - Avoid small parts and unsafe items for young children.
                  - Avoid adult themes/content for minors.
                - STRICTLY respect the budget:
                  - Only suggest gifts that can realistically be bought at or under the specified budget in the given region.
                  - If the budget is very low, favour small but thoughtful and creative ideas instead of unrealistic high-ticket items.
                - Be SPECIFIC, not generic:
                  - Suggest concrete products that a person could actually search for on Amazon.
                  - Prefer recognisable product lines and brands when possible (e.g. "Nintendo Switch Lite", "Fujifilm Instax Mini 12 Instant Camera", "Stanley Classic Quencher Tumbler", "Catan Board Game", not "(generic) Board Game".
                - Aim for VARIETY across the 10 ideas:
                  - Avoid 10 nearly identical items (e.g. five very similar board games).
                  - Vary categories where possible (e.g. one game, one hobby tool, one sentimental/keepsake item, one practical everyday item, one creative or experience-style item), as long as they still match the interests and goals.
                - Align with the goal type:
                  - If the goal is humour ("funny gift"), choose playful, light-hearted items that are funny but NOT offensive, cruel, or inappropriate.
                  - If the goal is sentimental ("something they will cherish forever"), prioritise keepsakes, customisable/meaningful gifts, and memory-making items that could have long-term emotional value.
                  - If the goal is enjoyment/utility ("something they will love" or "actually use"), prioritise high-utility items that fit their daily life or main hobbies and that they are realistically likely to use often.
                  - Do NOT default to the same brand or product type repeatedly (e.g. do not suggest LEGO sets unless they clearly match the interests or age group).
                  - Your suggestions MUST be grounded in the provided interests and goals, not generic toy ideas.
                  - Treat the "Interests / hobbies" as your primary guide: every gift should clearly relate to at least one of these interests.
                  - Avoid suggesting products that are only weakly related to the interests, even if they are popular gifts in general.

                
                AMAZON SEARCH TERM (CRITICAL RULES)
                - Every gift must be something that a shopper could plausibly find on Amazon in the specified region.
                - You must construct the "amazon_search_term" by combining:
                  1) Brand
                  2) Full Product Name
                  3) Model Number (if applicable)
                - The Model Number MUST be wrapped in double quotes.
                - - Correct example:
                  - "Fujifilm Instax Mini 12 Instant Camera 'Blush Pink'"
                - Incorrect examples:
                  - "LEGO \"42096\"" (too short, missing full product name)
                  - "LEGO Technic Porsche 42096" (model number not in quotes)
                - If there is NO clear or commonly used model number:
                  - Do NOT invent one.
                  - Just use Brand + Full Product Name (e.g. "Fujifilm Instax Mini 12 Instant Camera").
                
                FIELD-LEVEL GUIDELINES
                For each gift, follow these rules:
                
                - "gift_name":
                  - Short, clear, appealing display name.
                  - Should sound like a product title someone would recognise on a listing.
                  - Example: "LEGO Technic Porsche 911 RSR Car Model Kit".
                
                - "amazon_search_term":
                  - A search phrase that a user can paste directly into Amazon’s search bar.
                  - Must follow the AMAZON SEARCH TERM rules above.
                  - Do not add extra commentary or emojis.
                
                - "why_it_fits":
                  - ONE concise sentence.
                  - Clearly link the gift to the recipient’s age, interests, AND the stated goal.
                  - Example: "This detailed car model perfectly suits their love of motorsport and provides a satisfying, hands-on Christmas project."
                
                - "lasting_impact":
                  - ONE sentence.
                  - Describe the deeper, longer-term positive impact this gift can have on the recipient’s life, growth, relationships, or wellbeing.
                  - Go beyond the initial excitement of opening the gift and focus on how it will keep adding value over time.
                  - Adapt the angle to their age:
                    - For children: focus on curiosity, imagination, independence, learning through play, or bonding time with family.
                    - For teens: focus on identity, confidence, skill-building, creativity, aspirations, or positive social connection.
                    - For adults: focus on stress relief, daily quality of life, meaningful routines, learning or deepening a hobby, or making lasting memories with loved ones.
                
                - "buying_tip":
                  - ONE specific, actionable tip that helps them buy the right version.
                  - Examples:
                    - "Check the age rating and choose the set with at least 500 pieces for a longer build."
                    - "Make sure you select the Mini 12 model, not the older Mini 9."
                    - "Choose the correct size based on their usual UK shoe size."
                
                OUTPUT FORMAT (JSON ARRAY ONLY):
                [
                    {{
                        "category": "Creative / Tech / Outdoor (Pick one)",
                        "gift_name": "Specific Product Name",
                        "amazon_search_term": "Brand Name Product Name Model",
                        "reason": "Why it fits their interests",
                        "impact": "Long term benefit",
                        "buying_tip": "Specific check (e.g. check batteries)"
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

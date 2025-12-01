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
        "tag": "mcstarrstudio-21", 
        "currency": "$"
    },
        "United Kingdom (.co.uk)": {
        "domain": ".co.uk", 
        "tag": "mcstarrstudio-21",  # <--- Perfect!
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

st.set_page_config(page_title="AI Christmas Gift Idea Generator", page_icon="🎄", layout="centered")

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
        font-size: 22px;
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
st.title("🎄 AI Christmas Gift Idea Generator")
st.write("Generate a curated list of gift ideas based on the person's interests, your budget, and your goal for the present.")

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

    interests = st.text_area("Person's Interests", placeholder="e.g. Paw Patrol, muddy puddles, dinosaurs")
    goals = st.text_input("Goal of Gift", placeholder="e.g. Fun, Silly, Main gift that they will love")
    
    submitted = st.form_submit_button("Generate Gift List")

# --- MAIN LOGIC ---
if submitted:
    if not interests:
        st.warning("Please tell the generator what the person likes!")
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
                
                # 3. PROMPT (The Gold Standard Logic)
                prompt = f"""
You are an expert personal gift shopper, specialising in thoughtful, high-converting Christmas gifts.

Your task:
Use the inputs below to recommend exactly 5 specific gift ideas that feel tailored, age-appropriate, and genuinely impressive.

Inputs:
- Age: {age}
- Interests / hobbies: {interests}
- Gift goals: {goals} (e.g. "funny gift", "something they will love", "something they will cherish forever")
- Budget: {budget} (total budget for ONE gift, in the currency of the region)
- Region: {selected_region} (the country/market where the gift will be purchased)

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
  - Prefer recognisable product lines and brands when possible (e.g. "LEGO Technic Porsche 911 RSR" not "a car-themed LEGO set").
- Aim for VARIETY across the 5 ideas:
  - Avoid 5 nearly identical items (e.g. five very similar board games).
  - Vary categories where possible (e.g. one game, one hobby tool, one sentimental/keepsake item, one practical everyday item, one creative or experience-style item), as long as they still match the interests and goals.
- Align with the goal type:
  - If the goal is humour ("funny gift"), choose playful, light-hearted items that are funny but NOT offensive, cruel, or inappropriate.
  - If the goal is sentimental ("something they will cherish forever"), prioritise keepsakes, customisable/meaningful gifts, and memory-making items that could have long-term emotional value.
  - If the goal is enjoyment/utility ("something they will love" or "actually use"), prioritise high-utility items that fit their daily life or main hobbies and that they are realistically likely to use often.

AMAZON SEARCH TERM (CRITICAL RULES)
- Every gift must be something that a shopper could plausibly find on Amazon in the specified region.
- You must construct the "amazon_search_term" by combining:
  1) Brand
  2) Full Product Name
  3) Model Number (if applicable)
- The Model Number MUST be wrapped in double quotes.
- Correct example:
  - "LEGO Technic Porsche 911 RSR \"42096\""
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

OUTPUT FORMAT (STRICT)
- You must return ONLY valid JSON.
- No markdown, no backticks, no comments, no explanations.
- Return a JSON array of EXACTLY 5 objects.
- Use double quotes for all keys and string values.
- Do NOT include trailing commas.

Each object in the array MUST have exactly these keys and no others:
- "gift_name"
- "amazon_search_term"
- "why_it_fits"
- "lasting_impact"
- "buying_tip"

Return strictly JSON: 
[ 
{{ "gift_name": "Display Name (e.g. LEGO Technic Porsche 911 RSR)", 
"amazon_search_term": "Brand + Full Name + \"Model Number\" (e.g. LEGO Technic Porsche 911 RSR \"42096\")", 
"why_it_fits": "One sentence on why it fits the interests", 
"lasting_impact": "One sentence on the lasting_impact of gift", 
"buying_tip": "A specific tip (e.g. 'Ensure it is the Technic version')" }} 
] 
                """
                
                response = model.generate_content(prompt)
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                gift_data = json.loads(clean_text)

                st.subheader(f"🎁 Top Picks for {age}")

                # 4. DISPLAY LOOP
                for gift in gift_data:
                    name = gift.get('gift_name', 'Mystery Gift')
                    # Fallback: if AI fails to give search term, use name
                    search_term = gift.get('amazon_search_term', name) 
                    
                    reason = gift.get('why_it_fits', 'Fits your criteria perfectly.')
                    benefit = gift.get('developmental_benefit', 'Great for development.')
                    tip = gift.get('buying_tip', f"Look for the highest rated version of {name}")
                    
                    # Generate Regional Link using the OPTIMIZED Search Term
                    domain = region_data["domain"]
                    tag = region_data["tag"]
                    
                    # We encode the search term to be URL safe (quotes become %22)
                    encoded_search = urllib.parse.quote(search_term)
                    amazon_link = f"https://www.amazon{domain}/s?k={encoded_search}&tag={tag}"

                    # Layout
                    with st.container():
                        st.markdown(f"""
                        <div class="gift-card">
                            <div class="gift-title">{name}</div>
                            <div class="gift-reason">💡 {reason}</div>
                            <div class="gift-benefit">🎓 {benefit}</div>
                            <div class="pro-tip">✨ <strong>Pro Tip:</strong> {tip}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Button Label: We show the search term but remove quotes so it looks nice
                        clean_label = search_term.replace('"', '')
                        
                        st.link_button(
                            label=f"👉 Find '{clean_label}' on Amazon{domain}", 
                            url=amazon_link,
                            type="primary",
                            use_container_width=True
                        )
                        
                        st.write(" ") 

            except Exception as e:
                st.error(f"The Elves encountered a glitch: {e}")

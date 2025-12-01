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

st.set_page_config(
    page_title="AI Christmas Gift Idea Generator",
    page_icon="🎅",
    layout="centered"
)

# --- CSS STYLING ---
st.markdown(
    """
    <style>
    /* Overall app background – photo + dark overlay for readability */
    [data-testid="stAppViewContainer"] {
        background:
            linear-gradient(rgba(0,0,0,0.15), rgba(0,0,0,0.45)),
            url("https://images.pexels.com/photos/695971/pexels-photo-695971.jpeg")
            no-repeat center center fixed;
        background-size: cover;
    }

    /* Global text colours (override Streamlit's white text) */
    h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    label {
        color: #2c3e50 !important;   /* nice dark grey */
    }

    /* Make section headings (like "Top Picks") festive red */
    h2, h3 {
        color: #b22222 !important;
    }

    /* Make the header feel festive */
    h1 {
        font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
        text-align: center;
        color: #b22222;
        text-shadow: 0 2px 4px rgba(0,0,0,0.15);
        margin-bottom: 0.5rem;
    }

    /* Subtext under the title */
    .block-container p {
        text-align: center;
    }

    /* Gift card styling – like little presents */
    .gift-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 25px;
        border-radius: 18px;
        border: 2px solid #c0392b;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        margin-bottom: 25px;
        transition: transform 0.2s, box-shadow 0.2s;
        position: relative;
        overflow: hidden;
    }

    .gift-card::before {
        content: "";
        position: absolute;
        inset: 0;
        background:
            linear-gradient(#b71c1c, #b71c1c) 50% 0 / 4px 100% no-repeat,
            linear-gradient(#b71c1c, #b71c1c) 0 50% / 100% 4px no-repeat;
        opacity: 0.15;
        pointer-events: none;
    }

    .gift-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 24px rgba(0,0,0,0.15);
    }

    .gift-title {
        font-size: 22px;
        font-weight: 800;
        color: #b22222;
        margin-bottom: 10px;
    }

    .gift-reason {
        color: #2f4f4f;
        font-size: 16px;
        margin-bottom: 10px;
        border-left: 4px solid #27ae60;
        padding-left: 10px;
        background: #f0fff4;
    }

    .gift-benefit {
        color: #145a32;
        font-size: 15px;
        background: #e8f5e9;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 15px;
        border: 1px solid #c8e6c9;
    }

    .pro-tip {
        background: #fff7e6;
        border: 1px solid #f1c40f;
        color: #8e5b00;
        padding: 10px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 20px;
    }

    /* Form inputs & select – stop them being purple */
    .stTextInput > div > div > input,
    .stTextArea textarea,
    [data-baseweb="select"] > div {
        background-color: #ffffff !important;  /* box colour */
        color: #111827 !important;             /* text colour */
        border-radius: 12px;
        border: 1px solid #c0392b;             /* festive red border */
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }

    /* Hover / focus state */
    .stTextInput > div > div > input:focus,
    .stTextArea textarea:focus,
    [data-baseweb="select"] > div:focus-within {
        border: 2px solid #c0392b !important;
        box-shadow: 0 0 0 1px #c0392b33;
        outline: none;
    }

    /* Placeholder text colour */
    .stTextInput > div > div > input::placeholder,
    .stTextArea textarea::placeholder {
        color: #9ca3af;
    }

    /* Override ALL Streamlit buttons (including form submit) */
    .stButton > button,
    button[kind="primary"],
    button[kind="secondary"],
    button[data-testid="baseButton-secondaryFormSubmit"],
    button[data-testid="baseButton-primary"],
    a[role="button"] {
        background: linear-gradient(135deg, #c0392b, #e74c3c) !important;
        color: #ffffff !important;
        border-radius: 999px !important;
        border: none !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
    }

    .stButton > button:hover,
    button[kind="primary"]:hover,
    button[kind="secondary"]:hover,
    button[data-testid="baseButton-secondaryFormSubmit"]:hover,
    button[data-testid="baseButton-primary"]:hover,
    a[role="button"]:hover {
        background: linear-gradient(135deg, #a93226, #cd6155) !important;
        transform: translateY(-1px);
    }

    /* Optional: hide Streamlit menu/footer to keep it clean */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* SIMPLE SNOWFALL EFFECT */
    .snowflake {
        position: fixed;
        top: -10px;
        color: #ffffff;
        font-size: 18px;
        opacity: 0.85;
        pointer-events: none;
        animation-name: snowflakes-fall, snowflakes-shake;
        animation-duration: 10s, 3s;
        animation-timing-function: linear, ease-in-out;
        animation-iteration-count: infinite, infinite;
        z-index: 9999;
    }

    @keyframes snowflakes-fall {
        0% {top: -10%;}
        100% {top: 110%;}
    }

    @keyframes snowflakes-shake {
        0%, 100% {transform: translateX(0);}
        50% {transform: translateX(20px);}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- SNOWFLAKES ---
snowflakes = ""
for i in range(12):
    snowflakes += f"""
    <div class="snowflake" style="left: {8 * i}%; animation-delay: {0.7 * i}s;">
        ❄
    </div>
    """

st.markdown(snowflakes, unsafe_allow_html=True)

# --- HEADER ---
st.title("🎄 AI Christmas Gift Idea Generator")
st.write(
    "Tell the elves who you're shopping for, and get perfectly tailored Christmas gift ideas."
)

# --- INPUT FORM ---
with st.form("gift_form"):
    selected_region = st.selectbox("Select Amazon Region", list(AMAZON_CONFIG.keys()))
    region_data = AMAZON_CONFIG[selected_region]
    currency_symbol = region_data["currency"]

    col1, col2 = st.columns(2)
    with col1:
        age = st.text_input("Age Group", placeholder="e.g. 3 year old")
    with col2:
        budget = st.selectbox(
            "Budget",
            [
                "Any",
                f"Under {currency_symbol}20",
                f"{currency_symbol}20 - {currency_symbol}50",
                f"{currency_symbol}50+",
            ],
        )

    interests = st.text_area(
        "Person's Interests",
        placeholder="e.g. Paw Patrol, muddy puddles, dinosaurs",
    )
    goals = st.text_input(
        "Goal of Gift",
        placeholder="e.g. Fun, Silly, Main gift that they will love",
    )

    submitted = st.form_submit_button("🎁 Generate Gift List")

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
                model = genai.GenerativeModel("gemini-flash-latest")

                # 3. PROMPT (The Gold Standard Logic)
                prompt = f"""
ROLE: You are an expert personal gift shopper, specialising in thoughtful, high-converting Christmas gifts.

Your task:
Use the inputs below to recommend exactly 10 specific gift ideas that feel tailored, age-appropriate, and genuinely impressive.

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
  - Prefer recognisable product lines and brands when possible (e.g. "Nintendo Switch Lite", "Fujifilm Instax Mini 12 Instant Camera", "Stanley Classic Quencher Tumbler", "Catan Board Game", not "(generic) Board Game").
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
- Correct example:
  - "Fujifilm Instax Mini 12 Instant Camera 'Blush Pink'"
- Incorrect examples:
  - "LEGO "42096"" (too short, missing full product name)
  - "LEGO Technic Porsche 42096" (model number not in quotes)
- If there is NO clear or commonly used model number:
  - Do NOT invent one.
  - Just use Brand + Full Product Name (e.g. "Fujifilm Instax Mini 12 Instant Camera").

FIELD-LEVEL GUIDELINES
For each gift, follow these rules:

- "gift_name":
  - Short, clear, appealing display name.
  - Should sound like a product title someone would recognise on a listing.
  - Example: "Fujifilm Instax Mini 12 Instant Camera".

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
- Return a JSON array of EXACTLY 10 objects.
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
  {{
    "gift_name": "Display Name (e.g. Fujifilm Instax Instant Camera)",
    "amazon_search_term": "Brand + Full Name + \\"Model Number\\" (e.g. Fujifilm Instax Instant Camera \\"Mini 12\\")",
    "why_it_fits": "One sentence on why it fits the interests",
    "lasting_impact": "One sentence on the lasting_impact of gift",
    "buying_tip": "A specific tip (e.g. 'Ensure it is the Technic version')"
  }}
]
"""

                response = model.generate_content(prompt)
                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                gift_data = json.loads(clean_text)

                st.subheader(f"🎁 Top Picks for {age}")

                # 4. DISPLAY LOOP
                for gift in gift_data:
                    name = gift.get("gift_name", "Mystery Gift")
                    # Fallback: if AI fails to give search term, use name
                    search_term = gift.get("amazon_search_term", name)

                    reason = gift.get("why_it_fits", "Fits your criteria perfectly.")
                    benefit = gift.get("lasting_impact", "Great gift idea.")
                    tip = gift.get("buying_tip", f"Look for the highest rated version of {name}")

                    # Generate Regional Link using the OPTIMIZED Search Term
                    domain = region_data["domain"]
                    tag = region_data["tag"]

                    # We encode the search term to be URL safe (quotes become %22)
                    encoded_search = urllib.parse.quote(search_term)
                    amazon_link = f"https://www.amazon{domain}/s?k={encoded_search}&tag={tag}"

                    # Layout
                    with st.container():
                        st.markdown(
                            f"""
                            <div class="gift-card">
                                <div class="gift-title">{name}</div>
                                <div class="gift-reason">💡 {reason}</div>
                                <div class="gift-benefit">🎓 {benefit}</div>
                                <div class="pro-tip">✨ <strong>Pro Tip:</strong> {tip}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Button Label: We show the search term but remove quotes so it looks nice
                        clean_label = search_term.replace('"', "")

                        st.link_button(
                            label=f"👉 Find '{clean_label}' on Amazon{domain}",
                            url=amazon_link,
                            type="primary",
                            use_container_width=True,
                        )

                        st.write(" ")

            except Exception as e:
                st.error(f"The Elves encountered a glitch: {e}")

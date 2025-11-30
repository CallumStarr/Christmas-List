import streamlit as st
import google.generativeai as genai
import json
import urllib.parse
from duckduckgo_search import DDGS

# --- CONFIGURATION ---
# 1. Get your API Key here: https://aistudio.google.com/
# 2. Add your Amazon Affiliate Tag below
AMAZON_TAG = "your-tag-20"

st.set_page_config(page_title="Santa's AI Helper", page_icon="🎄", layout="centered")

# --- HELPER: SAFE IMAGE SEARCH ---
def get_safe_toy_image(toy_name):
    """
    Searches ONLY Amazon.com for the image to ensure relevance and safety.
    """
    try:
        with DDGS() as ddgs:
            # We restrict the search to amazon.com to avoid random internet images
            # We also turn SafeSearch to 'On' (Strict)
            query = f"site:amazon.com {toy_name} toy"
            results = list(ddgs.images(query, max_results=1, safesearch='On'))
            
            if results:
                return results[0]['image']
    except Exception:
        return None
    return None

# --- CSS STYLING ---
st.markdown("""
    <style>
    .gift-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 25px;
    }
    .gift-title {
        font-size: 20px;
        font-weight: 800;
        color: #2c3e50;
        margin-bottom: 5px;
    }
    .gift-reason {
        color: #666;
        font-style: italic;
        margin-bottom: 10px;
        font-size: 14px;
    }
    .gift-benefit {
        color: #2e86c1;
        font-size: 14px;
        background-color: #ebf5fb;
        padding: 8px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("🎄 Santa's AI Helper")
st.write("Enter the child's interests to generate a gift list.")

# --- INPUT FORM ---
with st.form("gift_form"):
    col1, col2 = st.columns(2)
    with col1:
        age = st.text_input("Age Group", placeholder="e.g. 3 year old")
    with col2:
        budget = st.selectbox("Budget", ["Any", "Under $20", "$20 - $50", "$50+"])

    interests = st.text_area("Child's Interests", placeholder="e.g. Paw Patrol, muddy puddles, dinosaurs")
    goals = st.text_input("Parent Goals", placeholder="e.g. Montessori, durable, quiet play")
    
    # NEW: Allow user to disable images if they want speed/cleanliness
    show_images = st.checkbox("Show Toy Images (Beta)", value=True)
    
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
                
                # 3. PROMPT
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
                        "why_it_fits": "Short reason",
                        "developmental_benefit": "Short benefit"
                    }}
                ]
                """
                
                response = model.generate_content(prompt)
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                gift_data = json.loads(clean_text)

                st.subheader(f"🎁 Top Picks for {age}")

                # 4. DISPLAY LOOP
                for gift in gift_data:
                    # A. Generate Amazon Search Link
                    search_term = urllib.parse.quote(gift['gift_name'])
                    amazon_link = f"https://www.amazon.com/s?k={search_term}&tag={AMAZON_TAG}"

                    # B. Fetch Image (Only if user checked the box)
                    img_url = None
                    if show_images:
                        img_url = get_safe_toy_image(gift['gift_name'])

                    # C. Layout
                    with st.container():
                        st.markdown(f"""
                        <div class="gift-card">
                            <div class="gift-title">{gift['gift_name']}</div>
                            <div class="gift-reason">💡 {gift['why_it_fits']}</div>
                            <div class="gift-benefit">🎓 {gift['developmental_benefit']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Layout based on whether we have an image
                        if show_images:
                            col_img, col_btn = st.columns([1, 2])
                            with col_img:
                                if img_url:
                                    st.image(img_url, width=150)
                                else:
                                    # Graceful fallback if no Amazon image found
                                    st.caption("No preview available")
                            with col_btn:
                                st.write(" ") 
                                st.write(" ") 
                                st.link_button(f"Buy {gift['gift_name']}", amazon_link, type="primary")
                        else:
                            # Simple layout if images are off
                            st.link_button(f"Buy {gift['gift_name']} on Amazon 🎁", amazon_link, type="primary")
                        
                        st.write("---")

            except Exception as e:
                st.error(f"The Elves encountered a glitch: {e}")

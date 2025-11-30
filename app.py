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

# --- HELPER: SMART IMAGE SEARCH ---
@st.cache_data(show_spinner=False)
def get_safe_toy_image(search_term):
    """
    Uses a simplified search term to find an image.
    Now with broader search settings to fix 'No Preview' issues.
    """
    try:
        with DDGS() as ddgs:
            # ATTEMPT 1: Search Amazon specifically (Best for white-background product shots)
            query_amazon = f"site:amazon.com {search_term}"
            results = list(ddgs.images(query_amazon, max_results=1))
            
            if results:
                return results[0]['image']
            
            # ATTEMPT 2: Broad Fallback (If Amazon fails)
            # Removed "white background" and strict filters to ensure we get SOMETHING.
            results_general = list(ddgs.images(search_term, max_results=1))
            
            if results_general:
                return results_general[0]['image']

    except Exception as e:
        print(f"Error fetching image for {search_term}: {e}")
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
st.write("Enter the child's interests to generate a visual gift list.")

# --- INPUT FORM ---
with st.form("gift_form"):
    col1, col2 = st.columns(2)
    with col1:
        age = st.text_input("Age Group", placeholder="e.g. 3 year old")
    with col2:
        budget = st.selectbox("Budget", ["Any", "Under $20", "$20 - $50", "$50+"])

    interests = st.text_area("Child's Interests", placeholder="e.g. Paw Patrol, muddy puddles, dinosaurs")
    goals = st.text_input("Parent Goals", placeholder="e.g. Montessori, durable, quiet play")
    
    # Checkbox to toggle images on/off
    show_images = st.checkbox("Show Toy Images", value=True)
    
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
                        "image_search_term": "Simple keywords to find an image (e.g. 'Magna-Tiles 100 piece')",
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
                    # Safely get data with defaults to prevent 'KeyError' crashes
                    name = gift.get('gift_name', 'Mystery Gift')
                    reason = gift.get('why_it_fits', 'Perfect for your criteria.')
                    benefit = gift.get('developmental_benefit', 'Great for development.')
                    
                    # Search term for image
                    img_search = gift.get('image_search_term', name)

                    # A. Generate Amazon Search Link
                    search_query_url = urllib.parse.quote(name)
                    amazon_link = f"https://www.amazon.com/s?k={search_query_url}&tag={AMAZON_TAG}"

                    # B. Fetch Image
                    img_url = None
                    if show_images:
                        img_url = get_safe_toy_image(img_search)

                    # C. Layout
                    with st.container():
                        st.markdown(f"""
                        <div class="gift-card">
                            <div class="gift-title">{name}</div>
                            <div class="gift-reason">💡 {reason}</div>
                            <div class="gift-benefit">🎓 {benefit}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Image and Button Layout
                        if show_images:
                            col_img, col_btn = st.columns([1, 2])
                            
                            with col_img:
                                if img_url:
                                    st.image(img_url, width=150)
                                else:
                                    # Graceful fallback if no image found
                                    st.markdown("## 🎁") 
                                    st.caption("No preview")
                                    
                            with col_btn:
                                st.write(" ") 
                                st.write(" ") 
                                st.link_button(
                                    label=f"Buy {name}", 
                                    url=amazon_link,
                                    type="primary"
                                )
                        else:
                            st.link_button(
                                label=f"Buy {name} on Amazon 🎁", 
                                url=amazon_link,
                                type="primary"
                            )
                        
                        st.write("---") # Separator

            except Exception as e:
                st.error(f"The Elves encountered a glitch: {e}")

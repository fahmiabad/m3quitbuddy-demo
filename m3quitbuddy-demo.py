import streamlit as st
from openai import OpenAI
import os

# --- RAG LIBRARIES (Updated imports) ---
# We use these to search our "Knowledge Base" for relevant Malaysian health info
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
# FIXED: Updated import path for recent LangChain versions
from langchain_core.documents import Document

# ================= CONFIGURATION =================
st.set_page_config(page_title="M3QuitBuddy", page_icon="🫁")

# CSS to make it look like a mobile chat app
st.markdown("""
<style>
    .stChatMessage { border-radius: 15px; padding: 10px; }
    .stButton button { width: 100%; border-radius: 20px; }
</style>
""", unsafe_allow_html=True)

# ================= SESSION STATE INIT =================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "step" not in st.session_state:
    st.session_state.step = "onboarding_age" 
if "profile" not in st.session_state:
    st.session_state.profile = {}

# ================= API SETUP =================
api_key = os.getenv("OPENAI_API_KEY")
if not api_key and "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]

if not api_key:
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    if not api_key:
        st.warning("Please enter an OpenAI API Key to continue.")
        st.stop()

client = OpenAI(api_key=api_key)

# ================= RAG KNOWLEDGE BASE (MALAYSIA CPG) =================
# In a real app, you would load this from a PDF file. 
# For this prototype, we simulate the Malaysian CPG content here.
MALAYSIA_CPG_TEXT = """
[TOPIC: VAPING / E-CIGARETTES]
In Malaysia, e-cigarettes and vaping products are NOT recommended as a smoking cessation aid (replacement therapy).
The Ministry of Health (MOH) maintains that vaping sustains nicotine addiction and introduces new chemical risks (e.g., EVALI).
Clinical advice: Advise patients to stop using both cigarettes and vapes completely. Do not suggest switching to vape to quit smoking.

[TOPIC: PHARMACOTHERAPY / MEDICATIONS]
First-line treatments approved in Malaysia include:
1. Nicotine Replacement Therapy (NRT): Available as Gum (2mg/4mg), Patch (15mg/10mg/5mg or 21mg/14mg/7mg), and Inhaler.
   - Protocol: Use for at least 8-12 weeks. Combination therapy (Patch + Gum) is more effective than single use.
2. Varenicline (Champix): Start 1 week before quit date. Dosing: 0.5mg daily (days 1-3), 0.5mg BD (days 4-7), then 1mg BD for 12 weeks.
   - Warning: Monitor for neuropsychiatric symptoms.
3. Bupropion SR: Start 1-2 weeks before quit date. 150mg daily (3 days), then 150mg BD.
   - Contraindication: History of seizures or eating disorders.

[TOPIC: BEHAVIOURAL THERAPY]
The 5Rs approach for those not ready to quit: Relevance, Risks, Rewards, Roadblocks, Repetition.
The STAR method for preparation: Set date, Tell family, Anticipate challenges, Remove tobacco.
Relapse Prevention: Identify triggers (stress, mamak sessions, boredom) and use 4Ds (Delay, Deep breath, Drink water, Distract).

[TOPIC: REFERRAL SERVICES]
mQuit Services: A public-private partnership accredited by MOH. Website: jomquit.my.
Klinik Kesihatan: Most government health clinics have a 'Klinik Berhenti Merokok'.
"""

@st.cache_resource
def setup_rag(api_key):
    """
    This function creates a searchable database (Vector Store) from the text above.
    It runs only once to save speed/cost.
    """
    # Using lightweight embeddings
    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    # Split the text into chunks based on the empty lines
    docs = [Document(page_content=chunk) for chunk in MALAYSIA_CPG_TEXT.split("\n\n") if chunk.strip()]
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore

# Initialize RAG
try:
    rag_engine = setup_rag(api_key)
    st.sidebar.success("📚 Local Health Data Loaded")
except Exception as e:
    st.sidebar.error(f"RAG Error: {e}")
    rag_engine = None

# ================= REVISED SYSTEM PROMPT =================
BASE_SYSTEM_PROMPT = """
Role & Identity:
You are M3QuitBuddy, a peer-support companion for Malaysian youth. 
Tone: Casual, 'Manglish', supportive.

INSTRUCTIONS:
1. RAG USAGE: You have access to context from Malaysian Clinical Practice Guidelines (CPG). 
   - If the CONTEXT provided below is relevant, USE IT to give accurate medical advice.
   - If the user asks about meds/vape, prioritize the CONTEXT over general knowledge.
   
2. GENERAL GUIDANCE:
   - VAPING: Not recommended in Malaysia. Advise quitting.
   - FRAMEWORK: Use STAR (Set, Tell, Anticipate, Remove) for planning.
   - CRISIS: Use 4Ds (Delay, Deep Breath, Drink Water, Distract).

SAFETY:
- Under 18: NO MEDS/NRT advice. Behavioral only.
- Suicide Risk: Refer Talian HEAL 15555 immediately.
"""

# ================= SIDEBAR (RESOURCES & SOS) =================
with st.sidebar:
    st.title("🫁 M3QuitBuddy")
    st.markdown("Your Malaysian Quit Smoking Companion.")
    st.divider()
    
    # SOS BUTTON
    st.error("🚨 GIAN TERUK? (SOS)")
    if st.button("BANTU SAYA SEKARANG"):
        sos_msg = (
            "🚨 **SOS MODE ACTIVATED** 🚨\n\n"
            "Relaks bro. Tarik nafas dalam-dalam... Hembus...\n\n"
            "**Buat '4D' ni sekarang:**\n"
            "1. 🧊 **Drink** air sejuk (Ice water).\n"
            "2. ⏳ **Delay** 5 minit je. Gian tu ombak, dia akan surut.\n"
            "3. 🎮 **Distract** (Main game, basuh muka).\n\n"
            "You boleh buat ni. Jangan kalah!"
        )
        st.session_state.messages.append({"role": "assistant", "content": sos_msg})
        st.rerun()

    st.divider()
    st.markdown("### 🏥 Resources")
    st.markdown("- **mQuit Services:** [jomquit.my](https://jomquit.my)")
    st.markdown("- **Talian HEAL:** 15555")
    
    if st.button("Reset Chat"):
        st.session_state.step = "onboarding_age"
        st.session_state.messages = []
        st.session_state.profile = {}
        st.rerun()

# ================= APP LOGIC FLOW =================

def handle_chat_response(user_input):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # --- RAG RETRIEVAL STEP ---
    retrieved_context = ""
    if rag_engine:
        # Search for the 2 most relevant chunks from our CPG text
        docs = rag_engine.similarity_search(user_input, k=2)
        retrieved_context = "\n\n".join([d.page_content for d in docs])
    
    # Build Prompt with Context
    profile_str = f"\nUSER PROFILE: Age {st.session_state.profile.get('age')}, Habit: {st.session_state.profile.get('habit')}."
    if st.session_state.profile.get('is_minor'):
        profile_str += " [WARNING: USER IS UNDER 18. NO MEDICATION ADVICE.]"

    # Inject the RAG context into the prompt
    full_prompt = f"{BASE_SYSTEM_PROMPT}\n\n{profile_str}\n\nRELEVANT MALAYSIAN GUIDELINES (CONTEXT):\n{retrieved_context}"

    messages = [{"role": "system", "content": full_prompt}] + st.session_state.messages

    # Generate AI Response
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True,
        )
        response = st.write_stream(stream)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

# --- STEP 1: AGE ---
if st.session_state.step == "onboarding_age":
    st.header("👋 Welcome, Bro/Sis!")
    st.write("Sebelum kita mula, nak kenal sikit boleh? (Data ni private, don't worry).")
    
    age = st.number_input("Umur berapa? (Age)", min_value=10, max_value=100, value=20)
    if st.button("Next ➡️", key="btn_age"):
        st.session_state.profile['age'] = age
        st.session_state.profile['is_minor'] = age < 18
        st.session_state.step = "onboarding_habit"
        st.rerun()

# --- STEP 2: HABIT ---
elif st.session_state.step == "onboarding_habit":
    st.header("🚬 What's your habit?")
    habit = st.radio("You layan apa sekarang?", 
                     ["Rokok (Cigarettes)", "Vape / Pod", "Dua-dua (Dual User)"])
    
    freq = st.text_input("Kerap mana? (e.g., '1 kotak sehari', '1 pod 3 hari')", "Sikit-sikit je")
    
    if st.button("Next ➡️", key="btn_habit"):
        st.session_state.profile['habit'] = habit
        st.session_state.profile['frequency'] = freq
        st.session_state.step = "onboarding_ready"
        st.rerun()

# --- STEP 3: READINESS ---
elif st.session_state.step == "onboarding_ready":
    st.header("💪 Readiness Check")
    st.write("Jujur je, 1-10, berapa ready you nak stop?")
    ready = st.slider("Scale", 1, 10, 5)
    
    if ready < 4:
        st.info("Takpe, tak ready takpa. Kita sembang santai je.")
    elif ready > 7:
        st.success("Fuh semangat! Jom kita try.")
        
    if st.button("Jom Sembang 💬", key="btn_ready"):
        st.session_state.profile['readiness'] = ready
        # Initial greeting from Bot
        greeting = f"Okay cun! Profile dah set. \n\nSo, apa plan? Nak try 'Cold Turkey' (berhenti terus) atau 'Slow-slow'? Atau nak tips elak gian?"
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        st.session_state.step = "chat_active"
        st.rerun()

# --- STEP 4: MAIN CHAT ---
elif st.session_state.step == "chat_active":
    st.subheader("💬 M3QuitBuddy")
    
    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Tanya apa je... (e.g., 'Nak try ubat patch?')"):
        handle_chat_response(prompt)

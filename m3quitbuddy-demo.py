import streamlit as st
from openai import OpenAI
import os

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
    st.session_state.step = "onboarding_age" # Start with onboarding
if "profile" not in st.session_state:
    st.session_state.profile = {}

# ================= API SETUP =================
# Try to get key from secrets, env, or user input
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    # Check Streamlit secrets
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        # Ask user in sidebar if no key found
        api_key = st.sidebar.text_input("OpenAI API Key", type="password")

if not api_key:
    st.warning("Please enter an OpenAI API Key in the sidebar to continue.")
    st.stop()

client = OpenAI(api_key=api_key)

# ================= SYSTEM PROMPT =================
BASE_SYSTEM_PROMPT = """
Role & Identity:
You are M3QuitBuddy, a supportive smoking cessation companion for Malaysian youth.
Tone: Friendly, uses 'Manglish' (Campur BM/English), slang like 'bro', 'lepak', 'gian'.
Core Goal: Help users quit using 5As (Ask, Advise, Assess, Assist, Arrange) and 5Rs.

Safety:
- If user < 18: DO NOT suggest NRT/Meds. Focus on behavioral tips only.
- Suicide/Self-Harm: IMMEDIATELY refer to Talian HEAL 15555 or Befrienders KL.
- Medical Emergency: Tell them to call 999.

Crisis Tips (4D):
1. Delay (Tunggu 5 minit)
2. Deep Breath (Tarik nafas)
3. Drink Water (Minum air sejuk)
4. Distract (Buat benda lain)
"""

# ================= SIDEBAR (RESOURCES & SOS) =================
with st.sidebar:
    st.title("🫁 M3QuitBuddy")
    st.markdown("Your Malaysian Quit Smoking Companion.")
    
    st.divider()
    
    # SOS BUTTON
    st.error("🚨 CRAVING ATTACK? (SOS)")
    if st.button("I NEED HELP NOW"):
        sos_msg = (
            "🚨 **SOS MODE ACTIVATED** 🚨\n\n"
            "Relaks bro/sis. Tarik nafas dalam-dalam... Hembus...\n\n"
            "**Try the 4D Trick now:**\n"
            "1. 🧊 **Drink** air sejuk.\n"
            "2. ⏳ **Delay** 5 minit je.\n"
            "3. 🎮 **Distract** diri (Main game kejap).\n\n"
            "You boleh buat ni. Jangan kalah dengan gian!"
        )
        st.session_state.messages.append({"role": "assistant", "content": sos_msg})
        st.rerun()

    st.divider()
    st.markdown("### 🏥 Resources")
    st.markdown("- **mQuit Services:** [jomquit.my](https://jomquit.my)")
    st.markdown("- **Talian HEAL:** 15555")
    st.markdown("- **Befrienders:** 03-7627 2929")
    
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

    # Build Prompt with Context
    profile_str = f"\nUSER CONTEXT: {st.session_state.profile}"
    messages = [{"role": "system", "content": BASE_SYSTEM_PROMPT + profile_str}] + st.session_state.messages

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
    st.write("Before we start, I need to know a bit about you to give the right advice.")
    
    age = st.number_input("Umur berapa? (Age)", min_value=10, max_value=100, value=20)
    if st.button("Next ➡️", key="btn_age"):
        st.session_state.profile['age'] = age
        st.session_state.profile['is_minor'] = age < 18
        st.session_state.step = "onboarding_habit"
        st.rerun()

# --- STEP 2: HABIT ---
elif st.session_state.step == "onboarding_habit":
    st.header("🚬 What's your habit?")
    habit = st.radio("You hisap apa sekarang?", 
                     ["Rokok (Cigarettes)", "Vape / Pod", "Dua-dua (Dual User)"])
    
    freq = st.text_input("How heavy? (e.g., '1 kotak sehari', '1 pod 2 hari')", "Sikit-sikit je")
    
    if st.button("Next ➡️", key="btn_habit"):
        st.session_state.profile['habit'] = habit
        st.session_state.profile['frequency'] = freq
        st.session_state.step = "onboarding_ready"
        st.rerun()

# --- STEP 3: READINESS ---
elif st.session_state.step == "onboarding_ready":
    st.header("💪 Readiness Check")
    ready = st.slider("On scale 1-10, how ready are you to quit?", 1, 10, 5)
    
    if ready < 4:
        st.info("It's okay not to be ready yet. We can just chat.")
    elif ready > 7:
        st.success("Semangat yang padu! Let's do this.")
        
    if st.button("Start Chatting 💬", key="btn_ready"):
        st.session_state.profile['readiness'] = ready
        # Initial greeting from Bot
        greeting = f"Alright profile set! ✅\n\nUmur: {st.session_state.profile['age']}, Habit: {st.session_state.profile['habit']}.\n\nSo bro/sis, apa yang paling susah pasal nak quit ni? Gian ke habit lepak?"
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        st.session_state.step = "chat_active"
        st.rerun()

# --- STEP 4: MAIN CHAT ---
elif st.session_state.step == "chat_active":
    st.subheader("💬 Chat with M3QuitBuddy")
    
    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Type something... (e.g., 'Aku stress la')"):
        handle_chat_response(prompt)

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

# ================= REVISED SYSTEM PROMPT (CRITICAL FIXES) =================
BASE_SYSTEM_PROMPT = """
Role & Identity:
You are M3QuitBuddy, a peer-support companion for Malaysian youth trying to quit smoking/vaping. 
Tone: Casual, supportive, uses 'Manglish' (Campur BM/English), slang like 'bro', 'lepak', 'gian', 'member'.

CORE GUIDELINES (USER-CENTRIC):
1. FRAMEWORK: Do NOT use "5 As" (that is for doctors). Use the "STAR" method for users:
   - S: Set a quit date.
   - T: Tell family/friends (for accountability).
   - A: Anticipate challenges (what triggers you?).
   - R: Remove cigarettes/vapes from your room/car.

2. MEDICAL ACCURACY (MALAYSIA CONTEXT):
   - VAPING: Vaping is NOT a recommended alternative to smoking in Malaysia. It still contains nicotine and harmful chemicals. Encourage quitting all nicotine products completely. If asked, say: "Vape bukan jalan keluar yang selamat, bro. Better kita aim bebas nikotin terus."
   - COLD TURKEY: It is SAFE to quit abruptly. Nicotine withdrawal is uncomfortable/stressful but NOT physically dangerous (unlike alcohol withdrawal). If a user asks, say it is safe but tough, and suggest coping tips.
   - SLOW REDUCTION (Tapering): Also a valid method. Let the user choose.
   - MEDICATIONS: If user < 18, DO NOT suggest NRT (patches/gum). Suggest behavioral tips (4Ds) only.

3. CRISIS TIPS (The 4Ds):
   - Delay (Tunggu 5 minit, craving will pass).
   - Deep Breath (Tarik nafas panjang).
   - Drink Water (Air sejuk shocked system).
   - Distract (Main game, scroll TikTok).

SAFETY ROUTING:
- Suicide/Self-Harm: "Bro, bunuh diri bukan jalan penyelesaian. Please call Talian HEAL 15555 or Befrienders 03-7627 2929 immediately."
- Severe Withdrawal (Shaking, hallucinations): Suggest seeing a doctor at Klinik Kesihatan.
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
    profile_str = f"\nUSER PROFILE: Age {st.session_state.profile.get('age')}, Habit: {st.session_state.profile.get('habit')}, Readiness: {st.session_state.profile.get('readiness')}/10."
    if st.session_state.profile.get('is_minor'):
        profile_str += " [WARNING: USER IS UNDER 18. NO MEDICATION ADVICE.]"

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
    if prompt := st.chat_input("Tanya apa je... (e.g., 'Bahaya ke stop mengejut?')"):
        handle_chat_response(prompt)

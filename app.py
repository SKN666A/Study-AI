import os
import sqlite3
import requests
import streamlit as st

# ---------------- API SETUP ----------------
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

# 1. Page Configuration & Cute Styling
st.set_page_config(
    page_title="Smart Study Buddy 🌸", page_icon="✨", layout="centered"
)


# ---------------- DATABASE LOGIC ----------------
def get_user_from_db():
  try:
    conn = sqlite3.connect("students.db")
    c = conn.cursor()
    c.execute(
        "SELECT username, class_val, score, mood, board, fav_sub, hate_sub,"
        " dp_avatar FROM users_v3 ORDER BY ROWID DESC LIMIT 1"
    )
    row = c.fetchone()
    conn.close()
    if row:
      return {
          "nick": row[0],
          "class": row[1],
          "score": row[2],
          "mood": row[3],
          "board": row[4],
          "fav_sub": row[5],
          "hate_sub": row[6],
          "dp": row[7],
      }
  except Exception:
    return None
  return None


# 2. Database Setup
conn = sqlite3.connect("students.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS users_v3 (
    username TEXT PRIMARY KEY, 
    class_val TEXT, 
    score TEXT, 
    mood TEXT, 
    board TEXT, 
    fav_sub TEXT, 
    hate_sub TEXT,
    dp_avatar TEXT
)
"""
)
conn.commit()

# ---------------- SESSION INITIALIZATION ----------------
if "registered" not in st.session_state:
  existing_user = get_user_from_db()
  if existing_user:
    st.session_state["registered"] = True
    st.session_state["user_profile"] = existing_user
    st.session_state["page"] = "chat_first"
  else:
    st.session_state["registered"] = False
    st.session_state["user_profile"] = {}
    st.session_state["page"] = "landing"

if "lang" not in st.session_state:
  st.session_state["lang"] = "EN"
if "chat_history" not in st.session_state:
  st.session_state["chat_history"] = []
if "show_balloons" not in st.session_state:
  st.session_state["show_balloons"] = False

# Trackers
if "user_nick" not in st.session_state:
  st.session_state["user_nick"] = ""
if "score_val" not in st.session_state:
  st.session_state["score_val"] = ""
if "fav_val" not in st.session_state:
  st.session_state["fav_val"] = ""
if "hate_val" not in st.session_state:
  st.session_state["hate_val"] = ""

txt_en = "Hey I am here to help you in study smartly and easily 😊"
txt_ur = (
    "Main aap ki parhai ko aasan aur smart banane me madad kar sakta hoon 😊"
)

# Custom CSS
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #fef6ff 0%, #f0f4ff 100%);
        color: #2d3748;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    label, .stMarkdown, p, span {
        color: #2d3748 !important;
        font-weight: 600 !important;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #2d3748 !important;
        border-radius: 12px !important;
        border: 1.5px solid #dcdde1 !important;
    }
    div[data-testid="stToast"] {
        background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%) !important;
        color: #ffffff !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 30px rgba(108, 92, 231, 0.4) !important;
        border: 2px solid #ffffff !important;
        padding: 15px !important;
    }
    div[data-testid="stToast"] * {
        color: #ffffff !important;
        font-size: 17px !important;
        font-weight: 800 !important;
    }
    .hero-title {
        font-size: 34px;
        font-weight: 800;
        text-align: center;
        background: -webkit-linear-gradient(45deg, #6c5ce7, #a29bfe, #fd79a8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 15px;
        margin-bottom: 10px;
    }
    .reaction-card {
        background: linear-gradient(90deg, #fd79a8, #a29bfe);
        color: white !important;
        padding: 12px 20px;
        border-radius: 15px;
        font-size: 16px;
        font-weight: 700;
        margin-top: -10px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(253, 121, 168, 0.3);
    }
    .reaction-card span {
        color: white !important;
    }
    .dp-circle {
        font-size: 65px;
        text-align: center;
        background: #ffffff;
        width: 100px;
        height: 100px;
        line-height: 95px;
        border-radius: 50%;
        margin: 10px auto;
        box-shadow: 0 8px 20px rgba(108, 92, 231, 0.25);
        border: 3px solid #a29bfe;
    }
    .stButton>button {
        border-radius: 25px !important;
        background: linear-gradient(90deg, #a29bfe 0%, #6c5ce7 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 10px 25px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(108, 92, 231, 0.2) !important;
    }
    .ai-face {
        font-size: 80px;
        text-align: center;
        margin: 10px 0px;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# REST API Response Engine (Gemini API)
def get_ai_response(user_prompt, profile_data):
  try:
    if profile_data:
      context = f"""
            System Instruction: You are a friendly, cute, and smart AI Study Buddy.
            Student Profile:
            - Name: {profile_data.get('nick')}
            - Class: {profile_data.get('class')}
            - Board: {profile_data.get('board')}
            - Favorite Subject: {profile_data.get('fav_sub')}
            - Weak/Hated Subject: {profile_data.get('hate_sub')}
            
            Always answer the student's questions accurately, simply, and helpfully in a warm tone (Roman Urdu + English).
            Give study tips, clear concepts, solve questions, and guide them according to their grade and subjects.
            """
    else:
      context = (
          "You are a friendly AI Study Coach. Keep replies encouraging, polite,"
          " and brief in Roman Urdu."
      )

    full_prompt = f"{context}\n\nUser Question: {user_prompt}"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": full_prompt}]}]}

    response = requests.post(url, json=payload)
    result = response.json()

    if "candidates" in result:
      return result["candidates"][0]["content"]["parts"][0]["text"]
    elif "error" in result:
      return f"API Error: {result['error']['message']}"
    else:
      return "Jawab process nahi ho saka, please retry karein."

  except Exception as e:
    return f"Network Issue: {e}"


# ---------------- PAGE ROUTING ----------------

# PAGE 1: LANDING PAGE
if st.session_state["page"] == "landing":
  display_text = txt_en if st.session_state.get("lang") == "EN" else txt_ur
  st.markdown(
      f"<div class='hero-title'>{display_text}</div>", unsafe_allow_html=True
  )
  st.write("")
  st.write("")

  col_center = st.columns([1, 2, 1])
  with col_center[1]:
    if st.button("✨ I am excited to start our study journey!"):
      st.session_state["page"] = "chat_first"
      st.rerun()

# PAGE 2: DYNAMIC CHAT PAGE
elif st.session_state["page"] == "chat_first":
  if st.session_state["show_balloons"]:
    st.balloons()
    st.session_state["show_balloons"] = False

  if st.session_state["registered"]:
    prof = st.session_state["user_profile"]
    st.markdown(
        f"<div class='dp-circle'>{prof.get('dp', '🤖').split()[0]}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h3 style='text-align: center; color: #6c5ce7;'>Welcome back,"
        f" {prof.get('nick', 'Student')}! ✨</h3>",
        unsafe_allow_html=True,
    )
  else:
    st.markdown("<div class='ai-face'>🤖✨</div>", unsafe_allow_html=True)
    st.markdown(
        "<h3 style='text-align: center; color: #6c5ce7;'>Hi! I am your AI"
        " Study Coach</h3>",
        unsafe_allow_html=True,
    )

  for msg in st.session_state["chat_history"]:
    with st.chat_message(msg["role"]):
      st.write(msg["text"])

  if (
      len(st.session_state["chat_history"]) == 0
      and not st.session_state["registered"]
  ):
    st.write("💡 Quick options:")
    p_col1, p_col2 = st.columns(2)
    with p_col1:
      if st.button("👋 Hello"):
        st.session_state["user_input_val"] = "Hello"
    with p_col2:
      if st.button("📋 I want to generate my study plan"):
        st.session_state["user_input_val"] = (
            "I want to generate my study plan"
        )

  user_input = st.chat_input("Koi bhi sawal ya topic poochnyein...")

  if "user_input_val" in st.session_state:
    user_input = st.session_state.pop("user_input_val")

  if user_input:
    st.session_state["chat_history"].append(
        {"role": "user", "text": user_input}
    )

    if not st.session_state["registered"]:
      bot_reply = (
          "Theek hy, main aap ki requirement samajh gaya hoon! Lekin agar aap"
          " pehle apni profile set kar lein to main aap ke subjects ke mutabiq"
          " sahi answers de sakoon ga. ✨"
      )
    else:
      with st.spinner("Thinking please wait... ✨"):
        bot_reply = get_ai_response(
            user_input, st.session_state["user_profile"]
        )

    st.session_state["chat_history"].append(
        {"role": "assistant", "text": bot_reply}
    )
    st.rerun()

  if (
      len(st.session_state["chat_history"]) > 0
      and not st.session_state["registered"]
  ):
    st.write("")
    if st.button("📝 Setup Profile Now"):
      st.session_state["page"] = "signup"
      st.rerun()

# PAGE 3: PROFILE SIGNUP
elif st.session_state["page"] == "signup":
  st.markdown(
      "<h2 style='text-align: center; color: #6c5ce7;'>🌸 Student Profile"
      " Setup</h2>",
      unsafe_allow_html=True,
  )

  dp_choice = st.selectbox(
      "Select Avatar DP 📸",
      [
          "🙋 Cyber Ninja",
          "💝 Master Scholar",
          "🐱 Cute Cat Learner",
          "🌟 Star Student",
          "😎 Cool AI Buddy",
          "👷 Boyish",
          "👲 Gentle man",
          "👯 Cutie",
          "😝 Facy",
          "😓 Confused",
          "👱 Girly",
          "🍟 Foodie",
          "😆 Smiling face",
          "😈 Magical Unicorn",
      ],
  )
  dp_icon = dp_choice.split()[0]
  st.markdown(f"<div class='dp-circle'>{dp_icon}</div>", unsafe_allow_html=True)

  nick = st.text_input("1. Your Nick Name (What should I call you? 😜)")
  if nick:
    if nick != st.session_state["user_nick"]:
      st.session_state["user_nick"] = nick
      st.toast(f"Nice name {nick}! 🥰", icon="✨")
    st.markdown(
        f"<div class='reaction-card'>✨ Nice name <b>{nick}</b>! 🥰</div>",
        unsafe_allow_html=True,
    )

  cls = st.selectbox(
      "2. What's your class?",
      ["10th Grade", "9th Grade", "11th Grade", "12th Grade", "Other Class"],
  )

  score = st.text_input(
      "3. Your previous class score? (e.g., 85% or Total Marks)"
  )
  if score:
    if score != st.session_state["score_val"]:
      st.session_state["score_val"] = score
      st.toast(f"Woah! {score} was a smarter score! Keep it up! 🎯", icon="👏")
    st.markdown(
        f"<div class='reaction-card'>👏 Woah! <b>{score}</b> was a smarter"
        " score!</div>",
        unsafe_allow_html=True,
    )

  mood = st.selectbox(
      "4. Your Study Mood",
      [
          "⚡ Fast & High Target (Cyber Ninja 🥷)",
          "🧘 Calm & Step-by-Step (Master Scholar 🦉)",
          "🎨 Creative & Visual Learner 🌈",
      ],
  )

  board = st.selectbox(
      "5. Education Board",
      [
          "Punjab Board",
          "Federal Board",
          "KPK Board",
          "Sindh Board",
          "Other Board",
      ],
  )

  fav_sub = st.text_input("6. Favorite Subject? ❤️")
  if fav_sub:
    if fav_sub != st.session_state["fav_val"]:
      st.session_state["fav_val"] = fav_sub
      st.toast(f"Oh! {fav_sub} is also liked by me! 💖", icon="📚")
    st.markdown(
        f"<div class='reaction-card'>💖 Oh! <b>{fav_sub}</b> is also liked by"
        " me!</div>",
        unsafe_allow_html=True,
    )

  hate_sub = st.text_input("7. Hated Subject? 🙈")
  if hate_sub:
    if hate_sub != st.session_state["hate_val"]:
      st.session_state["hate_val"] = hate_sub
      st.toast(
          f"Haha! 😝 Waise {hate_sub} mera bhi favorite nahi hai!", icon="😜"
      )
    st.markdown(
        f"<div class='reaction-card'>😝 Haha! Waise <b>{hate_sub}</b> mera"
        " bhi favorite nahi hai!</div>",
        unsafe_allow_html=True,
    )

  st.write("")
  if st.button("✨ Save & Complete Profile"):
    if nick and score and fav_sub and hate_sub:
      cursor.execute(
          "INSERT OR REPLACE INTO users_v3 VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
          (nick, cls, score, mood, board, fav_sub, hate_sub, dp_choice),
      )
      conn.commit()

      st.session_state["user_profile"] = {
          "nick": nick,
          "class": cls,
          "score": score,
          "mood": mood,
          "board": board,
          "fav_sub": fav_sub,
          "hate_sub": hate_sub,
          "dp": dp_choice,
      }
      st.session_state["registered"] = True
      st.session_state["show_balloons"] = True
      st.session_state["page"] = "chat_first"
      st.rerun()
    else:
      st.warning("Please saari fields fill kar ke Save button dabayein! 🌸")
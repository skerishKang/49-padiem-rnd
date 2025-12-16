import streamlit as st
import streamlit.components.v1 as components
import time
from datetime import datetime
import os
from frontend_unified.utils.translator import translate_text

st.set_page_config(
    page_title="AI 통역사",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS to Hide Streamlit Elements & match Theme ---
st.markdown("""
<style>
    /* Hide Streamlit Header & Footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Remove top padding */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 5rem;
    }
    
    /* Global Background */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Button Styling to match Purple Theme */
    div.stButton > button {
        background: linear-gradient(to bottom right, #4f46e5, #7c3aed);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
    }
    
    /* Secondary Button (Stop) */
    div.stButton > button:active {
        transform: scale(0.98);
    }
    
    /* Sticky Footer for Controls */
    div[data-testid="stVerticalBlock"]:has(div#fixed-bottom-controls) {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #0e1117;
        padding: 1.5rem 5rem; /* Increased side padding */
        z-index: 50;
        border-top: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        box-shadow: 0 -4px 20px rgba(0,0,0,0.3);
    }
    
    /* Adjust main content padding */
    .block-container {
        padding-bottom: 250px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Tailwind & Common Styles ---
TAILWIND_CDN = '<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>'
TAILWIND_CONFIG = """
<script>
  tailwind.config = {
    darkMode: "class",
    theme: {
      extend: {
        colors: {
          "primary": "#7c3aed",
          "background-dark": "#0e1117",
          "card-dark": "#262730",
        },
        fontFamily: {
          "display": ["Inter", "sans-serif"]
        },
      },
    },
  }
</script>
"""
COMMON_HEAD = f"""
<head>
    <meta charset="utf-8"/>
    {TAILWIND_CDN}
    {TAILWIND_CONFIG}
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet"/>
    <style>
        body {{ background-color: #0e1117; color: #e5e7eb; font-family: 'Inter', sans-serif; }}
        .material-symbols-outlined {{ font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }}
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: #0e1117; }}
        ::-webkit-scrollbar-thumb {{ background: #333; border-radius: 3px; }}
    </style>
</head>
"""

# --- HTML Generators ---

def render_header():
    return f"""
    <!DOCTYPE html>
    <html class="dark">
    {COMMON_HEAD}
    <body>
        <header class="flex items-center justify-between border-b border-white/10 px-6 py-4 bg-background-dark/50 backdrop-blur-md sticky top-0 z-50">
            <div class="flex items-center gap-3">
                <div class="size-8 text-primary flex items-center justify-center bg-white/5 rounded-lg">
                    <span class="material-symbols-outlined text-2xl">translate</span>
                </div>
                <h2 class="text-xl font-bold tracking-tight text-white">AI 통역사</h2>
            </div>
            <div class="flex gap-2">
                <button class="flex items-center justify-center size-10 rounded-full bg-white/5 hover:bg-white/10 transition-colors text-gray-300">
                    <span class="material-symbols-outlined">settings</span>
                </button>
                <button class="flex items-center justify-center size-10 rounded-full bg-white/5 hover:bg-white/10 transition-colors text-gray-300">
                    <span class="material-symbols-outlined">account_circle</span>
                </button>
            </div>
        </header>
    </body>
    </html>
    """

def render_conversation_display(transcripts, input_lang, output_lang):
    bubbles = ""
    if not transcripts:
        bubbles = f"""
        <div class="flex flex-col items-center justify-center h-full text-gray-500 gap-4 mt-20">
            <div class="size-16 rounded-full bg-white/5 flex items-center justify-center">
                <span class="material-symbols-outlined text-3xl">chat</span>
            </div>
            <p>대화를 시작해보세요.</p>
        </div>
        """
    
    for msg in transcripts:
        # Input (Left/Gray)
        bubbles += f"""
        <div class="flex justify-start max-w-[80%] mb-6">
            <div class="flex flex-col gap-1">
                <div class="px-5 py-3 rounded-2xl rounded-tl-none bg-card-dark border border-white/5 shadow-lg">
                    <p class="text-base text-gray-100 leading-relaxed">{msg['original']}</p>
                </div>
                <span class="text-xs text-gray-500 ml-2">{input_lang} • {msg['timestamp']}</span>
            </div>
        </div>
        """
        # Output (Right/Purple)
        bubbles += f"""
        <div class="flex justify-end max-w-[80%] self-end mb-6 ml-auto">
            <div class="flex flex-col gap-1 items-end">
                <div class="px-5 py-3 rounded-2xl rounded-tr-none bg-primary/20 border border-primary/30 shadow-lg">
                    <p class="text-base text-gray-100 leading-relaxed">{msg['translated']}</p>
                </div>
                <span class="text-xs text-primary/80 mr-2">{output_lang} • {msg['timestamp']}</span>
            </div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html class="dark">
    {COMMON_HEAD}
    <body class="bg-background-dark overflow-hidden">
        <div class="flex flex-col h-full p-4 overflow-y-auto" id="chat-container">
            {bubbles}
            <div id="bottom-anchor"></div>
        </div>
        <script>
            window.scrollTo(0, document.body.scrollHeight);
            var container = document.getElementById('chat-container');
            container.scrollTop = container.scrollHeight;
        </script>
    </body>
    </html>
    """

def render_speech_display(transcripts, input_lang, output_lang):
    left_content = ""
    right_content = ""
    
    if not transcripts:
        empty_state = """
        <div class="flex items-center justify-center h-40 text-gray-600">
            <p>연설 내용이 여기에 표시됩니다.</p>
        </div>
        """
        left_content = empty_state
        right_content = empty_state
    
    for msg in transcripts:
        left_content += f"""
        <div class="mb-4 p-4 rounded-xl bg-card-dark border border-white/5 hover:border-white/10 transition-colors">
            <p class="text-lg text-gray-100 leading-relaxed">{msg['original']}</p>
            <p class="text-xs text-gray-500 mt-2">{msg['timestamp']}</p>
        </div>
        """
        right_content += f"""
        <div class="mb-4 p-4 rounded-xl bg-primary/10 border border-primary/20 hover:bg-primary/15 transition-colors">
            <p class="text-lg text-gray-100 leading-relaxed">{msg['translated']}</p>
            <p class="text-xs text-primary/80 mt-2">{msg['timestamp']}</p>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html class="dark">
    {COMMON_HEAD}
    <body class="bg-background-dark overflow-hidden">
        <div class="grid grid-cols-2 gap-6 h-full p-4">
            <!-- Left Column: Source -->
            <div class="flex flex-col h-full bg-white/5 rounded-2xl border border-white/5 overflow-hidden">
                <div class="px-6 py-4 border-b border-white/5 bg-white/5 backdrop-blur flex items-center gap-2 sticky top-0">
                    <span class="size-2 rounded-full bg-gray-400"></span>
                    <h3 class="font-bold text-gray-200">{input_lang}</h3>
                </div>
                <div class="overflow-y-auto flex-1 p-4 space-y-2" id="left-col">
                    {left_content}
                </div>
            </div>
            
            <!-- Right Column: Target -->
            <div class="flex flex-col h-full bg-primary/5 rounded-2xl border border-primary/10 overflow-hidden">
                <div class="px-6 py-4 border-b border-primary/10 bg-primary/10 backdrop-blur flex items-center gap-2 sticky top-0">
                    <span class="size-2 rounded-full bg-primary"></span>
                    <h3 class="font-bold text-primary">{output_lang}</h3>
                </div>
                <div class="overflow-y-auto flex-1 p-4 space-y-2" id="right-col">
                    {right_content}
                </div>
            </div>
        </div>
        <script>
            var left = document.getElementById('left-col');
            var right = document.getElementById('right-col');
            left.scrollTop = left.scrollHeight;
            right.scrollTop = right.scrollHeight;
        </script>
    </body>
    </html>
    """

# --- Sidebar ---
with st.sidebar:
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("Home.py")
    
    st.markdown("---")
    st.header("설정 (Settings)")
    
    mode = st.radio(
        "모드 선택",
        ["대화 모드", "연설 모드"],
        index=0,
        captions=["채팅 형식 인터페이스", "좌우 분할 인터페이스"]
    )
    
    st.markdown("---")
    st.caption("기능 상태")
    st.toggle("실시간 번역", value=True)

# --- Main Layout ---

# 1. Custom Header (Static HTML)
components.html(render_header(), height=80, scrolling=False)

# 2. Language Controls (Moved from Sidebar)
st.markdown("<div style='margin-top: -10px;'></div>", unsafe_allow_html=True)
with st.container():
    col_lang1, col_lang2, col_lang_spacer = st.columns([1, 1, 2])
    with col_lang1:
        input_lang = st.selectbox("🗣️ 입력 언어 (Speaker)", ["한국어", "English", "日本語", "Español"], index=0, key="input_lang_select")
    with col_lang2:
        output_lang = st.selectbox("👂 출력 언어 (Listener)", ["English", "한국어", "日本語", "Español"], index=0, key="output_lang_select")

# 3. Session Data Management (Separated)
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "speech_history" not in st.session_state:
    st.session_state.speech_history = []

# 4. Display Area (Dynamic HTML)
if "대화" in mode:
    html_code = render_conversation_display(st.session_state.conversation_history, input_lang, output_lang)
    components.html(html_code, height=700, scrolling=False)
else:
    html_code = render_speech_display(st.session_state.speech_history, input_lang, output_lang)
    components.html(html_code, height=700, scrolling=False)

# 5. Controls (Streamlit)
st.markdown("<br>", unsafe_allow_html=True) # Spacer

# Container for all controls to keep them close
with st.container():
    # 1. Mic/Start Button & Input in one row
    col_mic, col_input = st.columns([1, 4])
    
    with col_mic:
        if "is_listening" not in st.session_state:
            st.session_state.is_listening = False
            
        btn_label = "⏹️ 중지" if st.session_state.is_listening else "🎤 시작"
        if st.button(btn_label, use_container_width=True):
            st.session_state.is_listening = not st.session_state.is_listening
            st.rerun()

    if st.session_state.is_listening:
        st.markdown("""
        <div style="text-align: center; color: #7c3aed; animation: pulse 2s infinite; margin-bottom: 5px; font-size: 0.8rem;">
            듣고 있는 중...
        </div>
        <style>
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        </style>
        """, unsafe_allow_html=True)


    with col_input:
        # 2. Message Input (Standard Input to control placement)
        def submit_message():
            user_input = st.session_state.user_input_widget
            if user_input:
                ts = datetime.now().strftime("%H:%M:%S")
                
                if "대화" in mode:
                    # Conversation Mode
                    from frontend_unified.utils.translator import translate_text_stream
                    
                    # Add User Message
                    st.session_state.conversation_history.append({
                        "original": user_input,
                        "translated": "...", 
                        "timestamp": ts
                    })
                    
                    # Stream Translation
                    full_translation = ""
                    stream = translate_text_stream(user_input, input_lang, output_lang)
                    for chunk in stream:
                        full_translation += chunk
                    
                    # Update
                    st.session_state.conversation_history[-1]["translated"] = full_translation

                else:
                    # Speech Mode
                    from frontend_unified.utils.translator import translate_text_stream
                    
                    # Add Entry
                    st.session_state.speech_history.append({
                        "original": user_input,
                        "translated": "", 
                        "timestamp": ts,
                        "audio": None
                    })
                    
                    # Stream
                    full_translation = ""
                    stream = translate_text_stream(user_input, input_lang, output_lang)
                    
                    status_placeholder = st.empty()
                    status_placeholder.toast(f"🔄 번역 중... ({output_lang})")
                    
                    for chunk in stream:
                        full_translation += chunk
                        st.session_state.speech_history[-1]["translated"] = full_translation
                        
                    # Final update
                    st.session_state.speech_history[-1]["translated"] = full_translation
                    
                    # Simulate TTS
                    status_placeholder.toast(f"🔊 음성 생성 중... ({output_lang})")
                    time.sleep(1) 
                    status_placeholder.toast(f"✅ 완료")

                # Clear input
                st.session_state.user_input_widget = ""

        st.text_input(
            "메시지 입력", 
            key="user_input_widget", 
            on_change=submit_message,
            placeholder="메시지를 입력하고 Enter를 누르세요...",
            label_visibility="collapsed"
        )

    # 3. Download Buttons
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    col_d1, col_d2, col_d3 = st.columns(3)

    def get_history_text(key):
        history = st.session_state.conversation_history if "대화" in mode else st.session_state.speech_history
        return "\n".join([f"[{m['timestamp']}] {m[key]}" for m in history])

    def get_full_history_text():
        history = st.session_state.conversation_history if "대화" in mode else st.session_state.speech_history
        return "\n".join([f"[{m['timestamp']}]\nOriginal: {m['original']}\nTranslated: {m['translated']}\n" for m in history])

    with col_d1:
        st.download_button("원문 다운로드", get_history_text("original"), "original.txt", use_container_width=True)
    with col_d2:
        st.download_button("번역문 다운로드", get_history_text("translated"), "translated.txt", use_container_width=True)
    with col_d3:
        st.download_button("전체 다운로드", get_full_history_text(), "full.txt", use_container_width=True)

    # Sticky Footer Marker
    st.markdown('<div id="fixed-bottom-controls"></div>', unsafe_allow_html=True)

import streamlit as st
import datetime
import base64
import os
import json
import uuid

# --- 페이지 설정 ---
st.set_page_config(page_title="가톨릭대학교 기숙사 나눔장터", layout="wide")

# --- CSS 스타일 적용 (상단 바 완벽 고정 및 스트림릿 기본 헤더 숨김) ---
st.markdown("""
    <style>
    .stApp { background-color: #F9FAFB; }
    
    /* 스트림릿 기본 상단 여백 및 햄버거 메뉴 강제 숨김 (우리가 만든 바가 최상단에 붙게 함) */
    header[data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 1rem !important; }
    
    /* 상단 UI 블록 강제 고정 */
    div[data-testid="stVerticalBlock"]:has(#sticky-header-anchor) {
        position: sticky !important;
        top: 0px !important;
        z-index: 99999 !important;
        background-color: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px) !important;
        padding: 15px 20px !important;
        border-bottom: 1px solid #E5E7EB !important;
        margin-bottom: 20px !important;
    }
    
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border-radius: 12px;
        background-color: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #F3F4F6;
    }
    </style>
""", unsafe_allow_html=True)

CATEGORIES = ["청소용품", "생활용품", "식품(미개봉)", "일회용품", "의류&잡화", "수납&정리용품", "학용품&책", "그 외 다른용품"]
DORMS = ["안드레아관", "스테파노관"]

# --- 💾 데이터베이스 로드 및 저장 ---
DATA_FILE = "data.json"

def load_data():
    data = {"users": {}, "items": [], "sessions": {}}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                data.update(loaded)
        except:
            pass
    return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if 'db' not in st.session_state:
    st.session_state.db = load_data()
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'reserving_item_id' not in st.session_state:
    st.session_state.reserving_item_id = None

# --- 자동 로그인(세션 토큰) 검증 및 만료 처리 ---
now = datetime.datetime.now()
valid_sessions = {}
for token, info in st.session_state.db.get('sessions', {}).items():
    try:
        if datetime.datetime.fromisoformat(info['expires']) > now:
            valid_sessions[token] = info
    except:
        pass

if len(valid_sessions) != len(st.session_state.db.get('sessions', {})):
    st.session_state.db['sessions'] = valid_sessions
    save_data(st.session_state.db)

if st.session_state.logged_in_user is None:
    if 'session' in st.query_params:
        url_token = st.query_params['session']
        if url_token in st.session_state.db['sessions']:
            st.session_state.logged_in_user = st.session_state.db['sessions'][url_token]['user_id']

# --- 로그인 / 회원가입 화면 ---
if st.session_state.logged_in_user is None:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A; margin-top: 50px;'>가톨릭대학교 기숙사 나눔장터</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab1, tab2 = st.tabs(["로그인", "회원가입"])
        with tab1:
            with st.form("login_form"):
                login_id = st.text_input("아이디")
                login_pw = st.text_input("비밀번호", type="password")
                auto_login = st.checkbox("자동 로그인 (10분 유지)", value=True)
                
                if st.form_submit_button("로그인", use_container_width=True):
                    if login_id in st.session_state.db['users'] and st.session_state.db['users'][login_id]['pw'] == login_pw:
                        st.session_state.logged_in_user = login_id
                        
                        if auto_login:
                            new_token = str(uuid.uuid4())
                            expire_time = (now + datetime.timedelta(minutes=10)).isoformat()
                            st.session_state.db['sessions'][new_token] = {'user_id': login_id, 'expires': expire_time}
                            save_data(st.session_state.db)
                            st.query_params['session'] = new_token
                            
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 틀렸습니다.")
        with tab2:
            with st.form("register_form"):
                reg_id = st.text_input("새 아이디")
                reg_pw = st.text_input("새 비밀번호", type="password")
                reg_dorm = st.selectbox("거주 기숙사 선택", DORMS)
                if st.form_submit_button("가입하기", use_container_width=True):
                    if reg_id in st.session_state.db['users']:
                        st.error("이미 존재하는 아이디입니다.")
                    elif not reg_id or not reg_pw:
                        st.warning("아이디와 비밀번호를 모두 입력해주세요.")
                    else:
                        st.session_state.db['users'][reg_id] = {'pw': reg_pw, 'dorm': reg_dorm}
                        save_data(st.session_state.db)
                        st.success("가입 완료! 로그인을 진행해주세요.")

# --- 메인 화면 ---
else:
    current_user_id = st.session_state.logged_in_user
    current_user_dorm = st.session_state.db['users'][current_user_id]['dorm']

    # --- 상단 UI (스크롤 시 고정 & 가톨릭대 로고 적용) ---
    header_container = st.container()
    with header_container:
        st.markdown("<div id='sticky-header-anchor'></div>", unsafe_allow_html=True)
        header_col1, header_col2, header_col3 = st.columns([3, 2, 1], vertical_alignment="center")
        with header_col1:
            # 전달받은 로고 이미지 파일 적용
            logo_path = "스크린샷 2026-11-10 오전 3.01.53.png"
            logo_html = "<h3 style='margin:0; color: #1E3A8A;'>가톨릭대학교</h3>" # 로고가 없을 때 텍스트 백업
            if os.path.exists(logo_path

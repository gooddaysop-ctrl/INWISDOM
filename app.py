import streamlit as st
import datetime
import base64
import os
import json

# --- 페이지 설정 ---
st.set_page_config(page_title="가톨릭대학교 기숙사 나눔장터", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F9FAFB; }
    .top-bar {
        background-color: white;
        padding: 15px 0px;
        border-bottom: 2px solid #E5E7EB;
        margin-bottom: 20px;
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

# --- 💾 데이터베이스 (JSON 파일) 로드 및 저장 함수 ---
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"users": {}, "items": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 세션 상태 초기화 (데이터 연동) ---
if 'db' not in st.session_state:
    st.session_state.db = load_data() # JSON 파일에서 가입자 및 물품 정보 불러오기
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False

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
                if st.form_submit_button("로그인", use_container_width=True):
                    # 파일에 저장된 유저 정보 대조
                    if login_id in st.session_state.db['users'] and st.session_state.db['users'][login_id]['pw'] == login_pw:
                        st.session_state.logged_in_user = login_id
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 틀렸습니다.")
                        
        with tab2:
            with st.form("register_form"):
                reg_id = st.text_input("새 아이디")
                reg_pw = st.text_input("새 비밀번호", type="password")
                reg_dorm = st.selectbox("거주 기숙사 선택 (해당 기숙사 물품만 거래 가능)", DORMS)
                if st.form_submit_button("가입하기", use_container_width=True):
                    if reg_id in st.session_state.db['users']:
                        st.error("이미 존재하는 아이디입니다.")
                    elif not reg_id or not reg_pw:
                        st.warning("아이디와 비밀번호를 모두 입력해주세요.")
                    else:
                        # 회원가입 성공 시 파일에 즉시 저장
                        st.session_state.db['users'][reg_id] = {'pw': reg_pw, 'dorm': reg_dorm}
                        save_data(st.session_state.db)
                        st.success("가입 완료! 로그인을 진행해주세요.")

# --- 메인 화면 ---
else:
    current_user_id = st.session_state.logged_in_user
    current_user_dorm = st.session_state.db['users'][current_user_id]['dorm']

    st.markdown("<div class='top-bar'>", unsafe_allow_html=True)
    header_col1, header_col2, header_col3 = st.columns([3, 2, 1])
    
    with header_col1:
        st.markdown(f"""
            <a href="?" target="_self" style="text-decoration: none;">
                <h3 style='margin:0; color: #1E3A8A;'>가톨릭대학교 기숙사 나눔장터 <span style='font-size:16px; color:#6B7280;'>({current_user_dorm})</span></h3>
            </a>
        """, unsafe_allow_html=True)
    
    with header_col2:
        search_query = st.text_input("검색", placeholder="어떤 물품을 찾으시나요?", label_visibility="collapsed")
    
    with header_col3:
        if st.button("➕ 물품 나눔하기", type="primary", use_container_width=True):
            st.session_state.show_add_form = not st.session_state.show_add_form
    st.markdown("</div>", unsafe_allow_html=True)

    image_path = "image_0f5c52.jpg"
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <div style="
                width: 100%; 
                height: 450px; 
                background-image: url('data:image/jpeg;base64,{img_base64}'); 
                background-size: cover; 
                background-position: center; 
                -webkit-mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 60%, rgba(0,0,0,0) 100%);
                mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 60%, rgba(0,0,0,0) 100%);
                margin-bottom: 20px;
            "></div>
        """, unsafe_allow_html=True)
    else:
        st.info("가톨릭대학교 전경 사진(image_0f5c52.jpg)을 app.py와 같은 폴더에 넣어주세요.")

    if st.session_state.show_add_form:
        with st.container(border=True):
            st.subheader("새 나눔 물품 등록")
            with st.form("add_item_form"):
                c1, c2 = st.columns(2)
                with c1:
                    item_name = st.text_input("물건 이름", placeholder="예: 미니 선풍기, 수납박스 2개")
                    item_category = st.selectbox("분류", CATEGORIES)
                    item_location = st.text_input("위치 (동/호실 또는 로비)", placeholder="예: 1층 로비, 302호 앞")
                with c2:
                    item_nickname = st.text_input("닉네임", placeholder="예: 302호 민지")
                    item_contact = st.text_input("연락 방법", placeholder="오픈채팅 링크, 호실 등")
                    item_image = st.file_uploader("사진 (선택)", type=['png', 'jpg', 'jpeg'])
                
                item_desc = st.text_area("상태·설명", placeholder="사용 기간, 상태, 수령 가능 시간 등")
                
                if st.form_submit_button("등록하기", type="primary", use_container_width=True):
                    if not item_name or not item_location or not item_nickname:
                        st.warning("물건 이름, 위치, 닉네임은 필수 항목입니다.")
                    else:
                        # 이미지를 base64 문자로 변환하여 저장
                        image_data = None
                        if item_image is not None:
                            image_data = base64.b64encode(item_image.read()).decode()

                        new_item = {
                            "id": len(st.session_state.db['items']) + 1,
                            "title": item_name,
                            "category": item_category,
                            "desc": item_desc,
                            "location": item_location,
                            "contact": item_contact,
                            "nickname": item_nickname,
                            "dorm": current_user_dorm,
                            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "image_data": image_data
                        }
                        # 새 물품 추가 후 파일에 즉시 저장
                        st.session_state.db['items'].insert(0, new_item)
                        save_data(st.session_state.db)
                        st.session_state.show_add_form = False
                        st.success("물품이 등록되었습니다!")
                        st.rerun()

    # 등록된 아이템 렌더링
    display_items = [
        item for item in st.session_state.db['items']
        if isinstance(item, dict) and item.get('dorm') == current_user_dorm
    ]
    
    if search_query:
        display_items = [
            item for item in display_items 
            if isinstance(item, dict) and (search_query.lower() in item.get('title', '').lower() or search_query.lower() in item.get('desc', '').lower())
        ]

    st.markdown("#### 🎁 실시간 나눔 목록")
    if not display_items:
        st.write("아직 올라온 나눔 물품이 없습니다. 첫 번째로 물건을 나눠보세요!")
    else:
        for i in range(0, len(display_items), 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < len(display_items):
                    item = display_items[i+j]
                    with cols[j]:
                        with st.container(border=True):
                            # base64 이미지 출력
                            if item.get('image_data'):
                                st.image(f"data:image/jpeg;base64,{item['image_data']}", use_column_width=True)
                            else:
                                st.markdown("<div style='height: 150px; background-color: #E5E7EB; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9CA3AF;'>이미지 없음</div>", unsafe_allow_html=True)
                            
                            st.markdown(f"**{item.get('title', '제목 없음')}**")
                            st.caption(f"{item.get('category', '미분류')} | {item.get('date', '')}")
                            st.write(f"📍 {item.get('location', '')}")
                            with st.expander("상세 보기"):
                                st.write(f"**설명:** {item.get('desc', '')}")
                                st.write(f"**연락처:** {item.get('contact', '')}")
                                st.write(f"**닉네임:** {item.get('nickname', '')}")

    st.sidebar.markdown(f"**{current_user_id}**님 환영합니다.")
    st.sidebar.markdown(f"🏠 소속: {current_user_dorm}")
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in_user = None
        st.rerun()

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

# --- 💾 데이터베이스 로드 및 저장 ---
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

if 'db' not in st.session_state:
    st.session_state.db = load_data()
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'reserving_item_id' not in st.session_state:
    st.session_state.reserving_item_id = None # 예약 진행 중인 아이템 ID 저장

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
                    if login_id in st.session_state.db['users'] and st.session_state.db['users'][login_id]['pw'] == login_pw:
                        st.session_state.logged_in_user = login_id
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

    # --- 상단 UI ---
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

    # --- 가톨릭대 사진 (Fade-out) ---
    image_path = "image_0f5c52.jpg"
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <div style="
                width: 100%; height: 450px; 
                background-image: url('data:image/jpeg;base64,{img_base64}'); 
                background-size: cover; background-position: center; 
                -webkit-mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 60%, rgba(0,0,0,0) 100%);
                mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 60%, rgba(0,0,0,0) 100%);
                margin-bottom: 20px;
            "></div>
        """, unsafe_allow_html=True)

    # --- 물품 등록 폼 ---
    if st.session_state.show_add_form:
        with st.container(border=True):
            st.subheader("새 나눔 물품 등록")
            with st.form("add_item_form"):
                c1, c2 = st.columns(2)
                with c1:
                    item_name = st.text_input("물건 이름", placeholder="예: 미니 선풍기")
                    item_category = st.selectbox("분류", CATEGORIES)
                    item_location = st.text_input("위치", placeholder="예: 1층 로비")
                with c2:
                    item_nickname = st.text_input("닉네임", placeholder="예: 302호 민지")
                    item_contact = st.text_input("연락 방법", placeholder="오픈채팅 링크 등")
                    item_image = st.file_uploader("사진", type=['png', 'jpg', 'jpeg'])
                item_desc = st.text_area("상태·설명")
                
                if st.form_submit_button("등록하기", type="primary", use_container_width=True):
                    if not item_name or not item_location or not item_nickname:
                        st.warning("물건 이름, 위치, 닉네임은 필수입니다.")
                    else:
                        image_data = base64.b64encode(item_image.read()).decode() if item_image else None
                        new_item = {
                            "id": len(st.session_state.db['items']) + 1,
                            "uploader_id": current_user_id, # 작성자 ID 추가
                            "title": item_name,
                            "category": item_category,
                            "desc": item_desc,
                            "location": item_location,
                            "contact": item_contact,
                            "nickname": item_nickname,
                            "dorm": current_user_dorm,
                            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "image_data": image_data,
                            "status": "available", # available, reserved, completed
                            "buyer_sid": "",
                            "buyer_contact": ""
                        }
                        st.session_state.db['items'].insert(0, new_item)
                        save_data(st.session_state.db)
                        st.session_state.show_add_form = False
                        st.rerun()

    # --- 물품 리스트 필터링 ---
    display_items = [i for i in st.session_state.db['items'] if isinstance(i, dict) and i.get('dorm') == current_user_dorm]
    if search_query:
        display_items = [i for i in display_items if search_query.lower() in i.get('title', '').lower() or search_query.lower() in i.get('desc', '').lower()]

    st.markdown("#### 🎁 실시간 나눔 목록")
    if not display_items:
        st.write("아직 올라온 물품이 없습니다.")
    else:
        for i in range(0, len(display_items), 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < len(display_items):
                    item = display_items[i+j]
                    with cols[j]:
                        with st.container(border=True):
                            # --- 1. 번개장터 스타일 이미지 오버레이 처리 ---
                            status = item.get('status', 'available')
                            overlay_html = ""
                            opacity = "1.0"
                            
                            if status == 'reserved':
                                opacity = "0.3"
                                overlay_html = '<div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); color:white; text-align:center; text-shadow:0px 2px 4px rgba(0,0,0,0.8);"><div style="font-size:36px;">🕒</div><div style="font-size:16px; font-weight:bold;">예약중</div></div>'
                            elif status == 'completed':
                                opacity = "0.3"
                                overlay_html = '<div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); color:white; text-align:center; text-shadow:0px 2px 4px rgba(0,0,0,0.8);"><div style="font-size:36px;">✅</div><div style="font-size:16px; font-weight:bold;">수령 완료</div></div>'

                            # 썸네일 렌더링
                            img_bg = f"data:image/jpeg;base64,{item['image_data']}" if item.get('image_data') else ""
                            if img_bg:
                                st.markdown(f'<div style="position:relative; width:100%; height:150px; background-color:black; border-radius:8px; overflow:hidden;"><img src="{img_bg}" style="width:100%; height:100%; object-fit:cover; opacity:{opacity};">{overlay_html}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div style="position:relative; width:100%; height:150px; background-color:#374151; border-radius:8px; overflow:hidden; display:flex; justify-content:center; align-items:center; color:#9CA3AF;"><div style="opacity:{opacity};">이미지 없음</div>{overlay_html}</div>', unsafe_allow_html=True)
                            
                            # --- 2. 기본 정보 ---
                            st.markdown(f"<div style='margin-top:10px;'><b>{item.get('title', '제목 없음')}</b></div>", unsafe_allow_html=True)
                            st.caption(f"{item.get('category')} | {item.get('date')}")
                            
                            # --- 3. 수령 기능 로직 ---
                            if status == 'available':
                                if item.get('uploader_id') != current_user_id: # 내 물건은 내가 예약 불가
                                    # 예약 폼 열기 버튼
                                    if st.button("✋ 수령하기", key=f"btn_{item['id']}", use_container_width=True):
                                        st.session_state.reserving_item_id = item['id']
                                        st.rerun()
                                    
                                    # 예약 폼 (해당 아이템에서 수령하기를 눌렀을 때만 나타남)
                                    if st.session_state.reserving_item_id == item['id']:
                                        with st.container(border=True):
                                            buyer_sid = st.text_input("학번", key=f"sid_{item['id']}")
                                            buyer_contact = st.text_input("연락처 (전화번호 등)", key=f"contact_{item['id']}")
                                            
                                            c1, c2 = st.columns(2)
                                            with c1:
                                                if st.button("✔️ 완료", type="primary", key=f"conf_{item['id']}", use_container_width=True):
                                                    if buyer_sid and buyer_contact:
                                                        # 데이터 업데이트 (예약중 상태로 변경)
                                                        for db_item in st.session_state.db['items']:
                                                            if db_item['id'] == item['id']:
                                                                db_item['status'] = 'reserved'
                                                                db_item['buyer_sid'] = buyer_sid
                                                                db_item['buyer_contact'] = buyer_contact
                                                                break
                                                        save_data(st.session_state.db)
                                                        st.session_state.reserving_item_id = None
                                                        st.rerun()
                                                    else:
                                                        st.warning("정보를 입력하세요.")
                                            with c2:
                                                if st.button("취소", key=f"canc_{item['id']}", use_container_width=True):
                                                    st.session_state.reserving_item_id = None
                                                    st.rerun()
                            
                            # 상세 내용 확장(Expander)
                            with st.expander("상세 보기"):
                                st.write(f"📍 위치: {item.get('location', '')}")
                                st.write(f"**설명:** {item.get('desc', '')}")
                                st.write(f"**닉네임:** {item.get('nickname', '')}")
                                st.write(f"**오픈채팅/연락처:** {item.get('contact', '')}")

    # --- 사이드바: 프로필 및 내 알림 센터 ---
    st.sidebar.markdown(f"**👤 {current_user_id}**님 환영합니다.")
    st.sidebar.markdown(f"🏠 소속: {current_user_dorm}")
    
    st.sidebar.divider()
    
    st.sidebar.markdown("### 🔔 내 물품 알림")
    my_items = [i for i in st.session_state.db['items'] if i.get('uploader_id') == current_user_id]
    has_notification = False
    
    for my_item in my_items:
        if my_item.get('status') == 'reserved':
            has_notification = True
            with st.sidebar.container(border=True):
                st.write(f"**{my_item['title']}** 예약 요청!")
                st.caption(f"학번: {my_item['buyer_sid']}")
                st.caption(f"연락처: {my_item['buyer_contact']}")
                if st.button("✅ 수락 (수령 완료처리)", key=f"accept_{my_item['id']}", use_container_width=True):
                    # 상태를 완료로 변경
                    for db_item in st.session_state.db['items']:
                        if db_item['id'] == my_item['id']:
                            db_item['status'] = 'completed'
                            break
                    save_data(st.session_state.db)
                    st.rerun()
                    
    if not has_notification:
        st.sidebar.caption("새로운 수령 예약 알림이 없습니다.")
    
    st.sidebar.divider()
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in_user = None
        st.rerun()

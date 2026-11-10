import streamlit as st
import datetime
import base64
import os
import json
import uuid

# --- 페이지 설정 ---
st.set_page_config(page_title="가톨릭대학교 기숙사 나눔장터", layout="wide", initial_sidebar_state="expanded")

# --- CSS 스타일 적용 ---
st.markdown("""
    <style>
    .stDeployButton { display: none !important; }
    #MainMenu { display: none !important; }
    .stApp { background-color: #F9FAFB; }
    
    /* 상단바 고정 (Sticky) */
    div[data-testid="stVerticalBlock"]:has(#sticky-header) {
        position: sticky;
        top: 2.875rem;
        background-color: #F9FAFB;
        z-index: 999;
        padding-top: 1rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #E5E7EB;
        margin-top: -1rem;
        margin-bottom: 1rem;
    }
    
    /* 사이드바 내부 버튼 */
    [data-testid="stSidebar"] button {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 1px solid #000000 !important;
        transition: all 0.2s;
    }
    [data-testid="stSidebar"] button:hover {
        background-color: #333333 !important;
        border-color: #333333 !important;
        color: #ffffff !important;
    }
    
    /* 물품 카드 디자인 */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border-radius: 12px;
        background-color: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #F3F4F6;
    }
    .logo-container:hover { opacity: 0.7; }
    </style>
""", unsafe_allow_html=True)

CATEGORIES = ["청소용품", "생활용품", "식품(미개봉)", "일회용품", "의류&잡화", "수납&정리용품", "학용품&책", "그 외 다른용품"]
DORMS = ["안드레아관", "스테파노관"]
DATA_FILE = "data.json"

def load_data():
    # chats 키 포함
    data = {"users": {}, "items": [], "sessions": {}, "chats": {}}
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

# 초기 세션 설정
if 'db' not in st.session_state:
    st.session_state.db = load_data()
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'reserving_item_id' not in st.session_state:
    st.session_state.reserving_item_id = None
if 'active_chat_id' not in st.session_state:
    st.session_state.active_chat_id = None

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

# --- 로그인 / 회원가입 ---
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

    # --- 상단바 고정 영역 ---
    header_container = st.container()
    with header_container:
        st.markdown("<div id='sticky-header'></div>", unsafe_allow_html=True)
        header_col1, header_col2, header_col3 = st.columns([3, 2, 1])
        
        with header_col1:
            logo_base64 = ""
            if os.path.exists("logo.png"):
                with open("logo.png", "rb") as f:
                    logo_base64 = base64.b64encode(f.read()).decode()
            
            if logo_base64:
                st.markdown(f"""
                    <a href="." target="_self" style="text-decoration: none; color: inherit;">
                        <div class="logo-container" style='display: flex; align-items: center; margin: 0; padding-top: 5px;'>
                            <img src='data:image/png;base64,{logo_base64}' style='height: 35px; margin-right: 12px; object-fit: contain;'>
                            <h3 style='margin:0; color: #1E3A8A;'>기숙사 나눔장터 <span style='font-size:16px; color:#6B7280;'>({current_user_dorm})</span></h3>
                        </div>
                    </a>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <a href="." target="_self" style="text-decoration: none; color: inherit;">
                        <div class="logo-container" style='display: flex; align-items: center; margin: 0; padding-top: 5px;'>
                            <h3 style='margin:0; color: #1E3A8A;'>가톨릭대학교 기숙사 나눔장터 <span style='font-size:16px; color:#6B7280;'>({current_user_dorm})</span></h3>
                        </div>
                    </a>
                """, unsafe_allow_html=True)
                
        with header_col2:
            search_query = st.text_input("검색", placeholder="어떤 물품을 찾으시나요?", label_visibility="collapsed")
            
        with header_col3:
            if st.button("➕ 물품 나눔하기", type="primary", use_container_width=True):
                st.session_state.show_add_form = not st.session_state.show_add_form
                st.session_state.active_chat_id = None 

    # --- 사이드바 ---
    st.sidebar.markdown(f"**👤 {current_user_id}**님 환영합니다.")
    st.sidebar.markdown(f"🏠 소속: {current_user_dorm}")
    st.sidebar.divider()
    
    # --- 사이드바: 1:1 채팅방 목록 ---
    st.sidebar.markdown("### 💬 1:1 채팅방")
    # 내가 올렸거나, 내가 수령하기로 한 물건 중 예약/완료 상태인 것 필터링
    my_chat_items = [i for i in st.session_state.db['items'] 
                     if i.get('status') in ['reserved', 'completed'] 
                     and (i.get('uploader_id') == current_user_id or i.get('buyer_id') == current_user_id)]
    
    if my_chat_items:
        for chat_item in my_chat_items:
            # 채팅 상대방 이름 표기
            other_person = chat_item['buyer_id'] if chat_item['uploader_id'] == current_user_id else chat_item['uploader_id']
            btn_label = f"📦 {chat_item['title'][:8]}.. ({other_person})"
            
            if st.sidebar.button(btn_label, key=f"chat_btn_{chat_item['id']}", use_container_width=True):
                st.session_state.active_chat_id = chat_item['id']
                st.session_state.show_add_form = False
                st.rerun()
    else:
        st.sidebar.caption("현재 참여 중인 채팅방이 없습니다.")

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
        if 'session' in st.query_params:
            url_token = st.query_params['session']
            if url_token in st.session_state.db.get('sessions', {}):
                del st.session_state.db['sessions'][url_token]
                save_data(st.session_state.db)
            del st.query_params['session']
        st.rerun()

    # --- 메인 화면 렌더링 분기점 ---
    
    # 1️⃣ 채팅방 렌더링
    if st.session_state.active_chat_id is not None:
        chat_id_str = str(st.session_state.active_chat_id)
        current_chat_item = next((i for i in st.session_state.db['items'] if i['id'] == st.session_state.active_chat_id), None)
        
        if current_chat_item:
            st.markdown(f"### 💬 [{current_chat_item['title']}] 1:1 채팅방")
            if st.button("⬅️ 메인으로 돌아가기"):
                st.session_state.active_chat_id = None
                st.rerun()
                
            st.divider()
            
            # 🔥 채팅창 부분만 2초마다 자동 새로고침(Polling)
            @st.fragment(run_every=2)
            def auto_refresh_chat(chat_id, user_id):
                # 파일에서 최신 데이터를 다시 불러옴
                fresh_db = load_data() 
                chat_history = fresh_db.get('chats', {}).get(chat_id, [])
                
                chat_container = st.container(height=400)
                with chat_container:
                    if not chat_history:
                        st.caption("아직 메시지가 없습니다. 인사를 건네보세요!")
                    for msg in chat_history:
                        is_me = (msg['sender'] == user_id)
                        with st.chat_message("user" if is_me else "assistant"):
                            st.markdown(f"**{msg['sender']}**")
                            st.write(msg['message'])
                            st.caption(msg['timestamp'])
            
            # 함수 실행하여 채팅창 렌더링
            auto_refresh_chat(chat_id_str, current_user_id)

            # 메시지 입력 (새로고침 구역 밖)
            if new_msg := st.chat_input("메시지를 입력하세요..."):
                # 내가 보내는 시점의 최신 DB 동기화
                st.session_state.db = load_data()
                
                if 'chats' not in st.session_state.db:
                    st.session_state.db['chats'] = {}
                if chat_id_str not in st.session_state.db['chats']:
                    st.session_state.db['chats'][chat_id_str] = []
                    
                st.session_state.db['chats'][chat_id_str].append({
                    "sender": current_user_id,
                    "message": new_msg,
                    "timestamp": datetime.datetime.now().strftime("%H:%M")
                })
                save_data(st.session_state.db)
                st.rerun()

    # 2️⃣ 장터 메인 화면 렌더링
    else:
        # 배경 이미지
        image_path = "image_0f5c52.jpg"
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                img_base64 = base64.b64encode(f.read()).decode()
            st.markdown(f"""
                <div style="
                    width: 100%; height: 350px; 
                    background-image: url('data:image/jpeg;base64,{img_base64}'); 
                    background-size: cover; background-position: center; 
                    -webkit-mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 50%, rgba(0,0,0,0) 100%);
                    mask-image: linear-gradient(to bottom, rgba(0,0,0,1) 50%, rgba(0,0,0,0) 100%);
                    margin-bottom: 20px;
                    border-radius: 12px;
                "></div>
            """, unsafe_allow_html=True)

        # 물품 등록 폼
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
                            new_id = 1 if not st.session_state.db['items'] else max([i['id'] for i in st.session_state.db['items']]) + 1
                            
                            new_item = {
                                "id": new_id,
                                "uploader_id": current_user_id,
                                "title": item_name,
                                "category": item_category,
                                "desc": item_desc,
                                "location": item_location,
                                "contact": item_contact,
                                "nickname": item_nickname,
                                "dorm": current_user_dorm,
                                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "image_data": image_data,
                                "status": "available",
                                "buyer_sid": "",
                                "buyer_contact": "",
                                "buyer_id": "" 
                            }
                            st.session_state.db['items'].insert(0, new_item)
                            save_data(st.session_state.db)
                            st.session_state.show_add_form = False
                            st.rerun()

        # 물품 리스트
        display_items = [i for i in st.session_state.db['items'] if isinstance(i, dict) and i.get('dorm') == current_user_dorm]
        if search_query:
            display_items = [i for i in display_items if search_query.lower() in i.get('title', '').lower() or search_query.lower() in i.get('desc', '').lower()]

        st.markdown("#### 🎁 실시간 나눔 목록")
        if not display_items:
            st.write("아직 올라온 물품이 없습니다. 상단의 '➕ 물품 나눔하기'를 눌러 첫 게시글을 올려보세요!")
        else:
            for i in range(0, len(display_items), 4):
                cols = st.columns(4)
                for j in range(4):
                    if i + j < len(display_items):
                        item = display_items[i+j]
                        with cols[j]:
                            with st.container(border=True):
                                status = item.get('status', 'available')
                                overlay_html = ""
                                opacity = "1.0"
                                
                                if status == 'reserved':
                                    opacity = "0.3"
                                    overlay_html = '<div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); color:white; text-align:center; text-shadow:0px 2px 4px rgba(0,0,0,0.8);"><div style="font-size:36px;">🕒</div><div style="font-size:16px; font-weight:bold;">예약중</div></div>'
                                elif status == 'completed':
                                    opacity = "0.3"
                                    overlay_html = '<div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); color:white; text-align:center; text-shadow:0px 2px 4px rgba(0,0,0,0.8);"><div style="font-size:36px;">✅</div><div style="font-size:16px; font-weight:bold;">수령 완료</div></div>'

                                img_bg = f"data:image/jpeg;base64,{item['image_data']}" if item.get('image_data') else ""
                                if img_bg:
                                    st.markdown(f'<div style="position:relative; width:100%; height:150px; background-color:black; border-radius:8px; overflow:hidden;"><img src="{img_bg}" style="width:100%; height:100%; object-fit:cover; opacity:{opacity};">{overlay_html}</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div style="position:relative; width:100%; height:150px; background-color:#374151; border-radius:8px; overflow:hidden; display:flex; justify-content:center; align-items:center; color:#9CA3AF;"><div style="opacity:{opacity};">이미지 없음</div>{overlay_html}</div>', unsafe_allow_html=True)
                                
                                st.markdown(f"<div style='margin-top:10px;'><b>{item.get('title', '제목 없음')}</b></div>", unsafe_allow_html=True)
                                st.caption(f"{item.get('category')} | {item.get('date')}")
                                
                                if status == 'available':
                                    if item.get('uploader_id') != current_user_id:
                                        if st.button("✋ 수령하기", key=f"btn_{item['id']}", use_container_width=True):
                                            st.session_state.reserving_item_id = item['id']
                                            st.rerun()
                                        
                                        if st.session_state.reserving_item_id == item['id']:
                                            with st.container(border=True):
                                                buyer_sid = st.text_input("학번", key=f"sid_{item['id']}")
                                                buyer_contact = st.text_input("연락처", key=f"contact_{item['id']}")
                                                
                                                c1, c2 = st.columns(2)
                                                with c1:
                                                    if st.button("✔️ 완료", type="primary", key=f"conf_{item['id']}", use_container_width=True):
                                                        if buyer_sid and buyer_contact:
                                                            for db_item in st.session_state.db['items']:
                                                                if db_item['id'] == item['id']:
                                                                    db_item['status'] = 'reserved'
                                                                    db_item['buyer_sid'] = buyer_sid
                                                                    db_item['buyer_contact'] = buyer_contact
                                                                    db_item['buyer_id'] = current_user_id # 구매자 ID 기록
                                                                    
                                                                    # 채팅방 생성 로직
                                                                    if 'chats' not in st.session_state.db:
                                                                        st.session_state.db['chats'] = {}
                                                                    if str(item['id']) not in st.session_state.db['chats']:
                                                                        st.session_state.db['chats'][str(item['id'])] = []
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
                                    else:
                                        if st.button("🗑️ 삭제하기", key=f"del_{item['id']}", use_container_width=True):
                                            st.session_state.db['items'] = [x for x in st.session_state.db['items'] if x['id'] != item['id']]
                                            save_data(st.session_state.db)
                                            st.rerun()
                                
                                with st.expander("상세 보기"):
                                    st.write(f"📍 위치: {item.get('location', '')}")
                                    st.write(f"**설명:** {item.get('desc', '')}")
                                    st.write(f"**작성자(닉네임):** {item.get('uploader_id')} ({item.get('nickname', '')})")
                                    st.write(f"**연락처:** {item.get('contact', '')}")

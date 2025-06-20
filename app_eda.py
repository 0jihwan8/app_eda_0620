import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")

        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload population_trends.csv file.")
            return

        df = pd.read_csv(uploaded)

        # '세종' 지역의 '-' 값 0으로 치환
        df.loc[df['지역'] == '세종'] = df.loc[df['지역'] == '세종'].replace('-', '0')

        # 숫자형 컬럼 변환
        numeric_cols = ['인구', '출생아수(명)', '사망자수(명)']
        for col in numeric_cols:
            df[col] = (
                df[col].astype(str)
                      .str.replace(',', '')
                      .replace('', '0')
                      .astype(float)
            )

        # 지역명 한글 → 영어 매핑
        region_map = {
            '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
            '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
            '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
            '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
            '제주': 'Jeju'
        }

        # Streamlit Tabs
        tabs = st.tabs(["Overview", "Nation Forecast", "5Y Region Change", "Top Diffs", "Pivot & Area Plot"])

        # Tab 1: 데이터 구조 및 요약
        with tabs[0]:
            st.header("DataFrame Info & Summary")

            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("Descriptive Statistics")
            st.write(df.describe())

        # Tab 2: 전국 데이터 예측
        with tabs[1]:
            st.header("Nation Forecast")

            nation_df = df[df['지역'] == '전국'].sort_values('연도')
            recent = nation_df.tail(3)
            recent_net_increase = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()

            last_year = nation_df['연도'].max()
            last_population = nation_df[nation_df['연도'] == last_year]['인구'].values[0]
            years_gap = 2035 - last_year
            predicted_population = last_population + recent_net_increase * years_gap

            fig, ax = plt.subplots()
            ax.plot(nation_df['연도'], nation_df['인구'], marker='o', label='Historical')
            ax.plot(2035, predicted_population, marker='s', color='red', label='2035 Forecast')
            ax.set_title("Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()

            st.pyplot(fig)

        # Tab 3: 최근 5년 지역별 변화량 및 변화율
        with tabs[2]:
            st.header("5-Year Region Population Change")

            region_df = df[df['지역'] != '전국'].copy()
            region_df['region_en'] = region_df['지역'].map(region_map)

            max_year = region_df['연도'].max()
            min_year = max_year - 5
            recent_df = region_df[region_df['연도'].isin([min_year, max_year])]

            pivot = recent_df.pivot(index='지역', columns='연도', values='인구').reset_index()
            pivot['change'] = pivot[max_year] - pivot[min_year]
            pivot['change_rate'] = (pivot['change'] / pivot[min_year]) * 100
            pivot['region_en'] = pivot['지역'].map(region_map)

            # 변화량 그래프
            pivot_sorted = pivot.sort_values('change', ascending=False)

            fig1, ax1 = plt.subplots(figsize=(8, 6))
            sns.barplot(x=pivot_sorted['change'] / 1000, y=pivot_sorted['region_en'], ax=ax1, palette='viridis')
            ax1.set_title("Population Change (k people)")
            ax1.set_xlabel("Change (k)")
            ax1.set_ylabel("Region")
            for i, v in enumerate(pivot_sorted['change'] / 1000):
                ax1.text(v, i, f"{v:.1f}k", va='center', ha='left', fontsize=9)
            st.pyplot(fig1)

            st.markdown("> Blue indicates growth, Red indicates decline.")

            # 변화율 그래프
            pivot_sorted_rate = pivot.sort_values('change_rate', ascending=False)
            fig2, ax2 = plt.subplots(figsize=(8, 6))
            sns.barplot(x=pivot_sorted_rate['change_rate'], y=pivot_sorted_rate['region_en'], ax=ax2, palette='coolwarm')
            ax2.set_title("Population Change Rate (%)")
            ax2.set_xlabel("Change Rate (%)")
            ax2.set_ylabel("Region")
            for i, v in enumerate(pivot_sorted_rate['change_rate']):
                ax2.text(v, i, f"{v:.2f}%", va='center', ha='left', fontsize=9)
            st.pyplot(fig2)

        # Tab 4: 연도별 증감 상위 100개
        with tabs[3]:
            st.header("Top 100 Yearly Changes")

            region_df = df[df['지역'] != '전국'].copy()
            region_df.sort_values(['지역', '연도'], inplace=True)
            region_df['증감'] = region_df.groupby('지역')['인구'].diff()

            top_diff = region_df.dropna().sort_values('증감', ascending=False).head(100)
            numeric_display = top_diff[['연도', '지역', '인구', '증감']].copy()

            styled_df = (
                numeric_display
                .style
                .format({'인구': '{:,.0f}', '증감': '{:,.0f}'})
                .background_gradient(subset=['증감'], cmap='bwr',
                                     vmin=-numeric_display['증감'].abs().max(),
                                     vmax=numeric_display['증감'].abs().max())
            )

            st.dataframe(styled_df, use_container_width=True)

        # Tab 5: 누적 영역 차트
        with tabs[4]:
            st.header("Pivot Table & Stacked Area Plot")

            region_df['region_en'] = region_df['지역'].map(region_map)
            pivot_table = region_df.pivot_table(index='연도', columns='region_en', values='인구', aggfunc='sum').fillna(0)

            st.subheader("Pivot Table")
            st.dataframe(pivot_table.style.format('{:,.0f}'), use_container_width=True)

            plt.figure(figsize=(12, 6))
            sns.set_palette("tab20")
            pivot_table.plot.area()
            plt.title("Population by Region Over Time")
            plt.xlabel("Year")
            plt.ylabel("Population")
            plt.legend(title="Region", loc='upper left', bbox_to_anchor=(1, 1))
            st.pyplot(plt.gcf())



# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
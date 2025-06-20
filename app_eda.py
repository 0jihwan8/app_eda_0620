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
        st.title("Population Trends EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded)

        # 전처리 수행: 세종 지역 결측치 처리 및 숫자 변환
        df.replace('-', np.nan, inplace=True)
        df.loc[df['Region'] == '세종'] = df.loc[df['Region'] == '세종'].fillna('0')

        for col in ['Population', '출생아수(명)', '사망자수(명)']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        tabs = st.tabs(["Basic Statistics", "Yearly Trends", "Regional Analysis", "Change Analysis", "Visualization"])

        # 1. 기초 통계
        with tabs[0]:
            st.header("Basic Statistics")
            st.subheader("DataFrame Info")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("Descriptive Statistics")
            st.dataframe(df.describe())

            st.subheader("Sample Data (Top 5 Rows)")
            st.dataframe(df.head())

        # 2. 연도별 추이
        with tabs[1]:
            st.header("Yearly Trends")
            if 'Year' in df.columns and 'Population' in df.columns:
                national = df[df['Region'] == '전국']
                national_yearly = national.groupby('Year')['Population'].sum().reset_index()

                recent_years = sorted(national_yearly['Year'].unique())[-3:]
                recent_data = national[national['Year'].isin(recent_years)]
                recent_births = recent_data.groupby('Year')['출생아수(명)'].sum()
                recent_deaths = recent_data.groupby('Year')['사망자수(명)'].sum()
                recent_net = (recent_births - recent_deaths).mean()

                last_population = national_yearly[national_yearly['Year'] == recent_years[-1]]['Population'].values[0]
                years_to_predict = 2035 - recent_years[-1]
                predicted_population = last_population + recent_net * years_to_predict

                national_yearly = national_yearly.append({"Year": 2035, "Population": predicted_population}, ignore_index=True)
                national_yearly = national_yearly.sort_values('Year')

                fig, ax = plt.subplots()
                sns.lineplot(data=national_yearly, x='Year', y='Population', marker='o', ax=ax)
                ax.set_title('Total Population Trend')
                ax.set_xlabel('Year')
                ax.set_ylabel('Population')
                ax.scatter(2035, predicted_population, color='red', label='Predicted 2035')
                ax.legend()
                st.pyplot(fig)
            else:
                st.warning("Year and Population columns are required.")

        # 3. 지역별 분석
        with tabs[2]:
            st.header("Regional Analysis")
            if {'Region', 'Year', 'Population'}.issubset(df.columns):
                regional_df = df[df['Region'] != '전국']

                region_map = {
                    '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
                    '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi', '강원': 'Gangwon',
                    '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk',
                    '경남': 'Gyeongnam', '제주': 'Jeju'
                }
                regional_df['Region_en'] = regional_df['Region'].map(region_map)

                latest_year = regional_df['Year'].max()
                past_year = latest_year - 5

                pivot = regional_df.pivot(index='Region_en', columns='Year', values='Population')
                pivot_diff = (pivot[latest_year] - pivot[past_year]) / 1000

                diff_df = pd.DataFrame({'Region': pivot_diff.index, 'Change': pivot_diff.values}).sort_values(by='Change', ascending=False)

                fig, ax = plt.subplots(figsize=(10,8))
                sns.barplot(data=diff_df, y='Region', x='Change', ax=ax)
                ax.set_title('5-Year Population Change')
                ax.set_xlabel('Change (thousand)')
                for i, v in enumerate(diff_df['Change']):
                    ax.text(v, i, f"{v:,.1f}", va='center')
                st.pyplot(fig)

                pivot_rate = ((pivot[latest_year] - pivot[past_year]) / pivot[past_year]) * 100
                rate_df = pd.DataFrame({'Region': pivot_rate.index, 'Rate (%)': pivot_rate.values}).sort_values(by='Rate (%)', ascending=False)

                fig2, ax2 = plt.subplots(figsize=(10,8))
                sns.barplot(data=rate_df, y='Region', x='Rate (%)', ax=ax2)
                ax2.set_title('5-Year Population Change Rate')
                ax2.set_xlabel('Rate (%)')
                for i, v in enumerate(rate_df['Rate (%)']):
                    ax2.text(v, i, f"{v:,.1f}%", va='center')
                st.pyplot(fig2)

                st.markdown("**Interpretation:** Regions like Sejong, Gyeonggi show significant population growth, while others decline, indicating demographic imbalance.")
            else:
                st.warning("Region, Year, and Population columns are required.")

        # 4. 변화량 분석
        with tabs[3]:
            st.header("Change Analysis")
            if {'Region', 'Year', 'Population'}.issubset(df.columns):
                regional_df = df[df['Region'] != '전국'].sort_values(['Region', 'Year'])
                regional_df['Diff'] = regional_df.groupby('Region')['Population'].diff()
                diff_records = regional_df.dropna(subset=['Diff']).copy()
                diff_records['Diff_thousand'] = (diff_records['Diff'] / 1000).round(1)
                diff_records['Diff_fmt'] = diff_records['Diff_thousand'].map(lambda x: f"{x:,.1f}")

                top_diff = diff_records.sort_values(by='Diff_thousand', ascending=False).head(100)
                display_df = top_diff[['Region', 'Year', 'Diff_thousand']].rename(columns={'Region': 'Region', 'Year': 'Year', 'Diff_thousand': 'Change (thousand)'}).reset_index(drop=True)

                def highlight(val):
                    color = 'background-color: #3498db' if val > 0 else 'background-color: #e74c3c'
                    return color

                st.dataframe(display_df.style.format({'Change (thousand)': '{:,.1f}'}).applymap(highlight, subset=['Change (thousand)']))
            else:
                st.warning("Region, Year, and Population columns are required.")

        # 5. 시각화
        with tabs[4]:
            st.header("Visualization (Stacked Area)")
            if {'Region', 'Year', 'Population'}.issubset(df.columns):
                region_map = {
                    '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
                    '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi', '강원': 'Gangwon',
                    '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk',
                    '경남': 'Gyeongnam', '제주': 'Jeju', '전국': 'Total'
                }
                df['Region_en'] = df['Region'].map(region_map)

                pivot_df = df.pivot_table(index='Year', columns='Region_en', values='Population', aggfunc='sum').fillna(0)
                pivot_df = pivot_df.drop(columns=['Total'], errors='ignore')

                plt.figure(figsize=(12, 8))
                colors = sns.color_palette("tab20", n_colors=pivot_df.shape[1])
                pivot_df.plot.area(color=colors)
                plt.title("Population Trends by Region")
                plt.xlabel("Year")
                plt.ylabel("Population")
                plt.legend(title="Region", loc="upper left")
                st.pyplot(plt.gcf())
            else:
                st.warning("Region, Year, and Population columns are required.")




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
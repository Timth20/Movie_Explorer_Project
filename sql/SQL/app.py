import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# -------------------------------------------
# 1. Database Configuration
# -------------------------------------------
DB_USER = 'root'
DB_PASS = 'huangwenge'
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_NAME = 'movie_explorer'

def get_connection():
    try:
        url = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(url)
        return engine.connect()
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# -------------------------------------------
# 2. Page & Style Settings
# -------------------------------------------
st.set_page_config(page_title="IMDb Explorer", page_icon="🎬", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { font-size: 18px !important; }
    [data-testid="stSidebar"] .stRadio label { font-size: 20px !important; }
    div.stButton > button { font-size: 16px; }
    .stTextArea textarea { font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------------------
# 3. Session State Management
# -------------------------------------------
if 'view_mode' not in st.session_state:
    st.session_state['view_mode'] = 'home'
if 'selected_id' not in st.session_state:
    st.session_state['selected_id'] = None
if 'random_movie' not in st.session_state:
    st.session_state['random_movie'] = None

def go_to_movie(tconst):
    st.session_state['view_mode'] = 'movie_detail'
    st.session_state['selected_id'] = tconst
    st.rerun()

def go_to_person(nconst):
    st.session_state['view_mode'] = 'person_detail'
    st.session_state['selected_id'] = nconst
    st.rerun()

def go_home():
    st.session_state['view_mode'] = 'home'
    st.rerun()

# -------------------------------------------
# 4. Data Functions
# -------------------------------------------
conn = get_connection()

def get_cast(tconst):
    query = text("""
        SELECT p.primaryName, p.nconst, pr.category 
        FROM principals pr
        JOIN people p ON pr.nconst = p.nconst
        WHERE pr.tconst = :tconst AND (pr.category LIKE 'act%')
        LIMIT 10
    """)
    return pd.read_sql(query, conn, params={"tconst": tconst})

def get_filmography(nconst):
    query = text("""
        SELECT m.primaryTitle, m.tconst, m.startYear, r.averageRating
        FROM principals pr
        JOIN movies m ON pr.tconst = m.tconst
        LEFT JOIN ratings r ON m.tconst = r.tconst
        WHERE pr.nconst = :nconst
        ORDER BY m.startYear DESC LIMIT 20
    """)
    return pd.read_sql(query, conn, params={"nconst": nconst})

# -------------------------------------------
# 5. UI Rendering
# -------------------------------------------

if conn:
    # --- VIEW: MOVIE DETAIL ---
    if st.session_state['view_mode'] == 'movie_detail':
        tconst = st.session_state['selected_id']
        if st.button("⬅️ Back to Home"):
            go_home()
            
        movie_q = text("SELECT * FROM movies WHERE tconst = :id")
        movie_df = pd.read_sql(movie_q, conn, params={"id": tconst})
        
        if not movie_df.empty:
            movie = movie_df.iloc[0]
            st.title(f"🎬 {movie['primaryTitle']}")
            st.caption(f"Year: {movie['startYear']} | Runtime: {movie['runtimeMinutes']} min | ID: {tconst}")
            
            st.subheader("🎭 Top Cast")
            cast_df = get_cast(tconst)
            if not cast_df.empty:
                cols = st.columns(4)
                for i, row in cast_df.iterrows():
                    with cols[i % 4]:
                        if st.button(f"👤 {row['primaryName']}", key=f"btn_cast_{row['nconst']}"):
                            go_to_person(row['nconst'])
            else:
                st.info("No cast information available.")

    # --- VIEW: PERSON DETAIL ---
    elif st.session_state['view_mode'] == 'person_detail':
        nconst = st.session_state['selected_id']
        if st.button("⬅️ Back to Home"):
            go_home()

        person_q = text("SELECT * FROM people WHERE nconst = :id")
        person_df = pd.read_sql(person_q, conn, params={"id": nconst})
        
        if not person_df.empty:
            person = person_df.iloc[0]
            st.title(f"👤 {person['primaryName']}")
            st.caption(f"Born: {person['birthYear']} | ID: {nconst}")
            
            st.subheader("🎥 Filmography")
            film_df = get_filmography(nconst)
            if not film_df.empty:
                for i, row in film_df.iterrows():
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"**{row['primaryTitle']}** ({row['startYear']})")
                    if c2.button("View", key=f"btn_film_{row['tconst']}"):
                        go_to_movie(row['tconst'])
                    st.divider()

    # --- VIEW: HOME ---
    else:
        st.title("🍿 IMDb Local Explorer")
        
        # 新增了 "💻 SQL Playground" 选项
        menu = st.sidebar.radio("Menu", [
            "📊 Top Rated", 
            "🔍 Search Movies", 
            "🌟 Search Stars", 
            "🎲 Random Pick",
            "💻 SQL Playground"
        ])

        # === Feature A: Top Rated ===
        if menu == "📊 Top Rated":
            st.header("🏆 Top Rated Movies (2015-2025)")
            year = st.slider("Select Year", 2015, 2025, 2023)
            query = text("""
                SELECT m.primaryTitle, m.startYear, r.averageRating, m.tconst 
                FROM movies m JOIN ratings r ON m.tconst = r.tconst
                WHERE m.startYear = :year AND r.numVotes > 5000
                ORDER BY r.averageRating DESC LIMIT 10
            """)
            df = pd.read_sql(query, conn, params={"year": year})
            for i, row in df.iterrows():
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"**{i+1}. {row['primaryTitle']}**")
                c2.write(f"⭐ {row['averageRating']}")
                if c3.button("Details", key=f"top_{row['tconst']}"):
                    go_to_movie(row['tconst'])

        # === Feature B: Search Movies ===
        elif menu == "🔍 Search Movies":
            st.header("🔎 Find a Movie")
            search = st.text_input("Enter title")
            if search:
                query = text("""
                    SELECT m.primaryTitle, m.startYear, m.tconst, r.averageRating 
                    FROM movies m LEFT JOIN ratings r ON m.tconst = r.tconst
                    WHERE m.primaryTitle LIKE :s LIMIT 15
                """)
                df = pd.read_sql(query, conn, params={"s": f"%{search}%"})
                for i, row in df.iterrows():
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"**{row['primaryTitle']}** ({row['startYear']}) - ⭐ {row['averageRating']}")
                    if c2.button("Details", key=f"src_{row['tconst']}"):
                        go_to_movie(row['tconst'])

        # === Feature C: Search Stars ===
        elif menu == "🌟 Search Stars":
            st.header("🌟 Find an Actor")
            name = st.text_input("Enter name")
            if name:
                query = text("SELECT primaryName, birthYear, nconst FROM people WHERE primaryName LIKE :s LIMIT 10")
                df = pd.read_sql(query, conn, params={"s": f"%{name}%"})
                for i, row in df.iterrows():
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"**{row['primaryName']}** ({row['birthYear']})")
                    if c2.button("Info", key=f"star_{row['nconst']}"):
                        go_to_person(row['nconst'])

        # === Feature D: Random Pick ===
        elif menu == "🎲 Random Pick":
            st.header("🎲 Random High-Rated Movie")
            
            if st.button("🎲 Pick a new movie for me"):
                query = text("""
                    SELECT m.primaryTitle, m.startYear, r.averageRating, m.tconst
                    FROM movies m JOIN ratings r ON m.tconst = r.tconst
                    WHERE r.averageRating > 7.5 AND m.startYear > 2000
                    ORDER BY RAND() LIMIT 1
                """)
                res = pd.read_sql(query, conn)
                if not res.empty:
                    st.session_state['random_movie'] = res.iloc[0]

            if st.session_state['random_movie'] is not None:
                mov = st.session_state['random_movie']
                st.success(f"We found: **{mov['primaryTitle']}**")
                col1, col2 = st.columns(2)
                col1.metric("Year", mov['startYear'])
                col2.metric("IMDb Rating", mov['averageRating'])
                st.markdown("---")
                st.write("Click below to see the **Cast & Crew**:")
                if st.button(f"👉 Go to {mov['primaryTitle']} Details Page"):
                    go_to_movie(mov['tconst'])

        # === Feature E: SQL Playground (新增功能) ===
        elif menu == "💻 SQL Playground":
            st.header("💻 Run Custom SQL Queries")
            st.markdown("Execute raw SQL queries")
            
            # 默认给一个示例查询，方便用户上手
            default_query = "SELECT * FROM movies ORDER BY startYear DESC LIMIT 10;"
            
            # 创建一个文本输入区域
            user_query = st.text_area("SQL Query:", value=default_query, height=150)
            
            col1, col2 = st.columns([1, 5])
            with col1:
                run_btn = st.button("▶️ Run Query", type="primary")
            
            if run_btn:
                if user_query.strip():
                    try:
                        # 尝试执行查询
                        # 使用 text() 包装 SQL 语句以确保安全
                        result_df = pd.read_sql(text(user_query), conn)
                        
                        st.success(f"Query executed successfully! Returned {len(result_df)} rows.")
                        st.dataframe(result_df, use_container_width=True)
                        
                    except Exception as e:
                        # 如果 SQL 有错（比如拼写错误），显示红色错误提示
                        st.error(f"❌ SQL Error: {e}")
                else:
                    st.warning("Please enter a SQL query first.")

    conn.close()
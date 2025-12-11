import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# -------------------------------------------
# 1. Database Configuration
# -------------------------------------------
DB_USER = 'root'
DB_PASS = 'password'  # Update with your password
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

# CSS to increase sidebar font size
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        font-size: 18px !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------------------
# 3. Session State Management (Navigation)
# -------------------------------------------
# We use session_state to track if we are looking at a Movie Detail or Person Detail
if 'view_mode' not in st.session_state:
    st.session_state['view_mode'] = 'home' # Options: home, movie_detail, person_detail
if 'selected_id' not in st.session_state:
    st.session_state['selected_id'] = None

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
# 4. Data Helper Functions
# -------------------------------------------
conn = get_connection()

def get_cast(tconst):
    """Fetch actors/actresses for a specific movie."""
    query = text("""
        SELECT p.primaryName, p.nconst, pr.category 
        FROM principals pr
        JOIN people p ON pr.nconst = p.nconst
        WHERE pr.tconst = :tconst AND (pr.category LIKE 'act%')
        LIMIT 10
    """)
    return pd.read_sql(query, conn, params={"tconst": tconst})

def get_filmography(nconst):
    """Fetch movies for a specific person."""
    query = text("""
        SELECT m.primaryTitle, m.tconst, m.startYear, r.averageRating
        FROM principals pr
        JOIN movies m ON pr.tconst = m.tconst
        LEFT JOIN ratings r ON m.tconst = r.tconst
        WHERE pr.nconst = :nconst
        ORDER BY m.startYear DESC
        LIMIT 20
    """)
    return pd.read_sql(query, conn, params={"nconst": nconst})

# -------------------------------------------
# 5. UI Rendering Logic
# -------------------------------------------

if conn:
    # --- VIEW: MOVIE DETAIL ---
    if st.session_state['view_mode'] == 'movie_detail':
        tconst = st.session_state['selected_id']
        if st.button("⬅️ Back to Home"):
            go_home()
            
        # Get Movie Info
        movie_q = text("SELECT * FROM movies WHERE tconst = :id")
        movie = pd.read_sql(movie_q, conn, params={"id": tconst}).iloc[0]
        
        st.title(f"🎬 {movie['primaryTitle']}")
        st.caption(f"Year: {movie['startYear']} | Runtime: {movie['runtimeMinutes']} min | ID: {tconst}")
        
        st.subheader("🎭 Top Cast")
        cast_df = get_cast(tconst)
        
        if not cast_df.empty:
            # Display cast as clickable buttons
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

        # Get Person Info
        person_q = text("SELECT * FROM people WHERE nconst = :id")
        person_df = pd.read_sql(person_q, conn, params={"id": nconst})
        
        if not person_df.empty:
            person = person_df.iloc[0]
            st.title(f"👤 {person['primaryName']}")
            st.caption(f"Born: {person['birthYear']} | ID: {nconst}")
            
            st.subheader("🎥 Filmography (Movies)")
            film_df = get_filmography(nconst)
            
            if not film_df.empty:
                # Display movies as clickable buttons (List view)
                for i, row in film_df.iterrows():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{row['primaryTitle']}** ({row['startYear']})")
                    with col2:
                        if st.button("View", key=f"btn_film_{row['tconst']}"):
                            go_to_movie(row['tconst'])
                    st.divider()
            else:
                st.info("No movies found for this person.")

    # --- VIEW: HOME (Dashboard) ---
    else:
        st.title("🍿 IMDb Local Explorer")
        
        # Sidebar Navigation
        menu = st.sidebar.radio("Menu", ["📊 Top Rated", "🔍 Search Movies", "🌟 Search Stars", "🎲 Random Pick"])

        # === Feature A: Top Rated (2015-2025) ===
        if menu == "📊 Top Rated":
            st.header("🏆 Top Rated Movies (2015-2025)")
            year = st.slider("Select Year", 2015, 2025, 2023)
            
            query = text("""
                SELECT m.primaryTitle, m.startYear, r.averageRating, r.numVotes, m.tconst
                FROM movies m
                JOIN ratings r ON m.tconst = r.tconst
                WHERE m.startYear = :year AND r.numVotes > 5000
                ORDER BY r.averageRating DESC LIMIT 10
            """)
            df = pd.read_sql(query, conn, params={"year": year})
            
            if not df.empty:
                # Custom Table with View Buttons
                for i, row in df.iterrows():
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"**{i+1}. {row['primaryTitle']}**")
                    c2.write(f"⭐ {row['averageRating']}")
                    if c3.button("Details", key=f"top_{row['tconst']}"):
                        go_to_movie(row['tconst'])
            else:
                st.warning("No data found for this year.")

        # === Feature B: Search Movies ===
        elif menu == "🔍 Search Movies":
            st.header("🔎 Find a Movie")
            search_term = st.text_input("Enter movie title", placeholder="e.g. Dune")
            
            if search_term:
                query = text("""
                    SELECT m.primaryTitle, m.startYear, m.tconst, r.averageRating 
                    FROM movies m
                    LEFT JOIN ratings r ON m.tconst = r.tconst
                    WHERE m.primaryTitle LIKE :search LIMIT 15
                """)
                df = pd.read_sql(query, conn, params={"search": f"%{search_term}%"})
                
                for i, row in df.iterrows():
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"**{row['primaryTitle']}** ({row['startYear']}) - ⭐ {row['averageRating']}")
                    if c2.button("Details", key=f"search_{row['tconst']}"):
                        go_to_movie(row['tconst'])

        # === Feature C: Search Stars ===
        elif menu == "🌟 Search Stars":
            st.header("🌟 Find an Actor/Acture")
            name_term = st.text_input("Enter name", placeholder="e.g. Timothée")
            
            if name_term:
                query = text("SELECT primaryName, birthYear, nconst FROM people WHERE primaryName LIKE :search LIMIT 10")
                df = pd.read_sql(query, conn, params={"search": f"%{name_term}%"})
                
                for i, row in df.iterrows():
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"**{row['primaryName']}** (Born: {row['birthYear']})")
                    if c2.button("Filmography", key=f"star_{row['nconst']}"):
                        go_to_person(row['nconst'])

        # === Feature D: Random Pick ===
        elif menu == "🎲 Random Pick":
            st.header("🎲 Random High-Rated Movie")
            if st.button("Pick for me"):
                query = text("""
                    SELECT m.primaryTitle, m.startYear, r.averageRating, m.tconst
                    FROM movies m JOIN ratings r ON m.tconst = r.tconst
                    WHERE r.averageRating > 7.5 AND m.startYear > 2000
                    ORDER BY RAND() LIMIT 1
                """)
                res = pd.read_sql(query, conn)
                if not res.empty:
                    mov = res.iloc[0]
                    st.success(f"We found: {mov['primaryTitle']}")
                    # Direct navigation button
                    if st.button(f"Check out {mov['primaryTitle']} Details"):
                        go_to_movie(mov['tconst'])

    conn.close()
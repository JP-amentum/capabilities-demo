import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

import sqlite3
import hashlib
import altair as alt
from datetime import datetime
import os
from functools import partial

# --- Password Hashes ---
VIEWER_PASSWORD = "a031faaa259fb838388c52358bd295b06cefaf784df98000e9cff353c27fda4f" # 'amentum2025'
ADMIN_PASSWORD = "0e89f223e226ae63268cf39152ab75722e811b89d29efb22a852f1667bd22ae0"  # 'admin2025'

# --- Colourful Titles ---
st.markdown("""
    <style>
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #39B54A;
    }
    </style>
""", unsafe_allow_html=True)

# --- Change Sidebar Colours ---
st.markdown("""
    <style>
    /* Sidebar background */
    section[data-testid="stSidebar"] {
        background-color: #000000;
    }
    /* Sidebar text*/
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    /* Sidebar buttons */
    section[data-testid="stSidebar"] button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid #000000 !important;
    }
    /* Button hover effect */
    section[data-testid="stSidebar"] button:hover {
        background-color: #39B54A !important;
        color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Auth ---
if "role" not in st.session_state:
    st.session_state.role = None

if not st.session_state.role:
    st.title("🔐 Login to Amentum CapabilityConnect")
    pwd = st.text_input("Enter password", type="password")
    hashed = hashlib.sha256(pwd.encode()).hexdigest()
    if hashed == VIEWER_PASSWORD:
        st.session_state.role = "viewer"
        st.rerun()
    elif hashed == ADMIN_PASSWORD:
        st.session_state.role = "admin"
        st.rerun()
    elif pwd:
        st.error("Incorrect password.")
    st.stop()
    
if "page" not in st.session_state:
    st.session_state.page = "Home"

if "search_term" not in st.session_state:
    st.session_state.search_term = ""

if "trigger_rerun" not in st.session_state:
    st.session_state.trigger_rerun = False

if st.session_state.trigger_rerun:
    st.session_state.trigger_rerun = False
    st.rerun()

def reset_page():
        st.session_state.page = "Search"

def set_search_term(value):
    st.session_state.search_term = value
    st.session_state.trigger_rerun = True
    
# --- SQLite Setup ---
DB_FILE = "capabilities.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                competency TEXT,
                skill TEXT,
                description TEXT,
                cap_group TEXT,
                group_capability TEXT,
                global_sme TEXT,
                sme_env TEXT,
                sme_energy TEXT,
                sme_das TEXT,
                sme_tci TEXT,
                sme_apac TEXT,
                key_words TEXT
            )
        """)
init_db()

def load_data_from_db():
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql_query("SELECT * FROM capabilities", conn)

def insert_data(df):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM capabilities")
        df.to_sql("capabilities", conn, if_exists="append", index=False)

# --- Navigation ---
st.sidebar.image("Amentum_Logo_White_H.png", use_container_width=True)
st.sidebar.title("Navigation")

st.sidebar.markdown("""
    <hr style="border:none; height: 3px; background-color: #39B54A; margin-top: -10px; margin-bottom: 20px;">
""", unsafe_allow_html=True)

pages_admin = ["Home", "Admin", "Search", "Explorer", "US Reachback", "Dashboard", "Feedback"]
pages_user = ["Home", "Search", "Explorer", "US Reachback", "Feedback"]
pages = pages_admin if st.session_state.role == "admin" else pages_user

for p in pages:
    if st.session_state.page == p:
        st.sidebar.markdown(f"**➡ {p}**")
    else:
        if st.sidebar.button(p):
            st.session_state.page = p
            st.rerun()
            
# --- Admin Page ---
if st.session_state.page == "Admin":
    st.title("🛠 Admin Panel")

    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        # Clear old data before inserting
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("DELETE FROM capabilities")

        xls = pd.ExcelFile(uploaded_file, engine="openpyxl")
        exclude = ["Info", "Level Definitions", "Definitions", "Sheet2"]
        all_data = []
        for sheet in xls.sheet_names:
            if sheet in exclude:
                continue
            try:
                df = xls.parse(sheet, skiprows=2)
                df.columns = [str(c).strip().replace('\xa0', ' ') for c in df.columns]
                df["Domain"] = sheet
                all_data.append(df)
            except Exception:
                continue

        raw_df = pd.concat(all_data, ignore_index=True)
        raw_df.columns = [c.strip() for c in raw_df.columns]

        mapped_df = pd.DataFrame({
            "domain": raw_df["Domain"],
            "competency": raw_df.get("Competency", ""),
            "skill": raw_df.get("Skill", ""),
            "description": raw_df.get("Description", ""),
            "cap_group": raw_df.get("Unnamed: 7", ""),
            "group_capability": raw_df.get("Unnamed: 8", ""),
            "global_sme": raw_df.get("Head of Profession", ""),
            "sme_env": raw_df.get("Environment", ""),
            "sme_energy": raw_df.get("Energy", ""),
            "sme_das": raw_df.get("D&AS", ""),
            "sme_tci": raw_df.get("TC&I", ""),
            "sme_apac": raw_df.get("APAC", ""),
            "key_words": raw_df.get("Keywords", "")
        })

        insert_data(mapped_df)
        st.success("✅ Data uploaded and stored in database.")

    st.markdown("### ✏️ Edit Capabilities")
    db_df = load_data_from_db()

    admin_search = st.text_input("Search capabilities to edit")
    if admin_search:
        db_df = db_df[
            db_df["skill"].str.contains(admin_search, case=False, na=False) |
            db_df["competency"].str.contains(admin_search, case=False, na=False)
        ]

    for i, row in db_df.iterrows():
        with st.expander(f"🧠 {row['skill']} — {row['domain']}"):
            with st.form(f"edit_form_{row['id']}"):
                new_data = {
                    "domain": st.text_input("Domain", row["domain"], key=f"domain_{i}"),
                    "competency": st.text_input("Competency", row["competency"], key=f"competency_{i}"),
                    "skill": st.text_input("Skill", row["skill"], key=f"skill_{i}"),
                    "description": st.text_area("Description", row["description"], key=f"description_{i}"),
                    "cap_group": st.text_input("Capability Group", row["cap_group"], key=f"cap_group_{i}"),
                    "group_capability": st.text_input("Group Capability", row["group_capability"], key=f"group_cap_{i}"),
                    "global_sme": st.text_input("Global SME", row["global_sme"], key=f"global_sme_{i}"),
                    "sme_env": st.text_input("SME - Environment", row["sme_env"], key=f"sme_env_{i}"),
                    "sme_energy": st.text_input("SME - Energy", row["sme_energy"], key=f"sme_energy_{i}"),
                    "sme_das": st.text_input("SME - D&AS", row["sme_das"], key=f"sme_das_{i}"),
                    "sme_tci": st.text_input("SME - TC&I", row["sme_tci"], key=f"sme_tci_{i}"),
                    "sme_apac": st.text_input("SME - APAC", row["sme_apac"], key=f"sme_apac_{i}")
                }
                submitted = st.form_submit_button("Save changes")
                if submitted:
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("""
                            UPDATE capabilities SET
                                domain = ?, competency = ?, skill = ?, description = ?,
                                cap_group = ?, group_capability = ?, global_sme = ?,
                                sme_env = ?, sme_energy = ?, sme_das = ?, sme_tci = ?, sme_apac = ?
                            WHERE id = ?
                        """, (*new_data.values(), row["id"]))
                    st.success("Changes saved.")

# --- Home Page ---
elif st.session_state.page == "Home":
    st.title("Welcome to CapabilityConnect!")
    st.text("CapabilityConnect is the primary search and discovery tool for capabilities in Amentum E&E-I")
    st.text("Please select one of the options below")
    def navigate(page_name):
        st.session_state.page = page_name
        st.rerun()
    col1, col2, col3 = st.columns([3, 3, 3])

    with col1:
        if st.button("🔍 Search", use_container_width=True):
            navigate("Search")
            
    with col2:
        if st.button("📚 Explorer", use_container_width=True):
            navigate("Explorer")

    with col3:
        if st.button("💬 Feedback", use_container_width=True):
            navigate("Feedback")

    col4, col5, col6 = st.columns([3, 3, 3])
    with col5:
        st.image("Amentum_Logo_V.png", use_container_width=True)

            
# --- Search Page ---
   
elif st.session_state.page == "Search":
   
    st.title("🔍 Capability Search")
    df = load_data_from_db()
    domains = df["domain"].dropna().unique()
    st.text_input("Search for a skill or competency", key="search_term", on_change=reset_page)
    selected_domains = st.multiselect("Filter by Discipline(s)", options=domains)

    if st.session_state.search_term or selected_domains:
        if st.session_state.search_term:
            filtered = df[
                df["skill"].str.contains(st.session_state.search_term, case=False, na=False) |
                df["competency"].str.contains(st.session_state.search_term, case=False, na=False) |
                df["key_words"].str.contains(st.session_state.search_term, case=False, na=False) |
                df["cap_group"].str.contains(st.session_state.search_term, case=False, na=False)
            ]
        else:
            filtered = df.copy()
    
        if selected_domains :
            filtered = filtered[filtered["domain"].isin(selected_domains)]
    
        
        st.markdown(f"**🔎 {len(filtered)} result(s) found.**") #Shows number of search results

        if filtered.empty:
            st.warning("No results found.")
        else:
            grouped = filtered.groupby("domain")
            for domain, group in grouped:
                st.markdown(f"## 🏷️ {domain}")
                for _, row in group.iterrows():
                    st.markdown(f"### 🧠 {row['skill']}")
                    st.markdown(f"- **Competency:** {row['competency']}")
                    st.markdown(f"- **Description:** {row['description'] or '*No description available*'}")
                    col3, col4 = st.columns([1, 3])
                    with col3:
                        st.markdown(f"- **Capability:**")
                    with col4:
                        st.button(
                            f"`{row['cap_group']}`",
                            key=f"cap_group_btn_{_}",
                            on_click=partial(set_search_term, row['cap_group'])
                        )
                    col3, col4 = st.columns([1, 3])
                    with col3:
                        st.markdown(f"- **Capability Group:**")
                    with col4:
                        st.button(f"`{row['group_capability']}`", key=f"group_capability_btn_{_}")
                    st.markdown(f"- **👤 Head of Profession:** `{row['global_sme'] or 'TBC'}`")
                    st.markdown("- **👥 Divisional Contacts:**")
                    st.markdown(f"  - Environment: `{row['sme_env'] or 'TBC'}`")
                    st.markdown(f"  - Energy: `{row['sme_energy'] or 'TBC'}`")
                    st.markdown(f"  - D&AS: `{row['sme_das'] or 'TBC'}`")
                    st.markdown(f"  - TC&I: `{row['sme_tci'] or 'TBC'}`")
                    st.markdown(f"  - APAC: `{row['sme_apac'] or 'TBC'}`")
                    st.markdown("---")
    else:
        st.info("Please enter a search term or select a filter to see results.")

# --- Explorer Page ---
elif st.session_state.page == "Explorer":
    st.text_input("Search for a capability")
    st.title("Capability Title: Lorem Ipsum ")
    st.markdown("**Executive Summary**: 2-3 sentences max.")
    st.markdown(" ")
    st.markdown("### Supporting Skills")
    st.markdown("    - Skill 1")
    st.markdown("    - Skill 2")
    st.markdown("    - Skill 3")
    st.markdown(" ")
    st.markdown("### Differentiators")
    st.markdown("**Proprietary Tools and Tech:**")
    st.markdown("    - Software 1")
    st.markdown("    - Tool 2")
    st.markdown("    - Software 2")
    st.markdown("    - Laboratory 1")
    st.markdown("**Certifications and Accreditations:**")
    st.markdown("    - ISO Accreditations")
    st.markdown("    - Others")
    st.markdown("**Additional Information:**")
    st.markdown(" ")
    st.markdown("### Case Studies:")
    st.markdown("    - Example Projects")
    st.markdown(" ")
    st.markdown("### Compliance to Codes and Standards")
    st.markdown("    - List of codes and standards")
    st.markdown(" ")
    st.markdown("### Points of Contact")
    st.markdown("    - **Head of Profession**: Joe Bloggs")
    st.markdown("    - **SME**: Jane Doe")
    st.markdown("    - **Divisional Contact**: John Smith")
    
    
    
    #df = load_data_from_db()
    #df = df.dropna(how='all')
    
    #if df.empty:
        #st.warning("No data found. Admins must upload a capability file.")
        #st.stop()

    #domain = st.selectbox("Select a discipline", sorted(df["domain"].dropna().unique()))
    #filtered = df[df["domain"].str.strip().str.lower() == domain.strip().lower()]

    #st.markdown(f"**🔎 {len(filtered)} result(s) found.**") #Shows number of search results

    #for _, row in filtered.iterrows():
        #st.markdown(f"### 🧠 {row['skill']}")
        #st.markdown(f"- **Competency:** {row['competency']}")
        #st.markdown(f"- **Description:** {row['description'] or '*No description*'}")
        #st.markdown(f"- **Capability Group:** `{row['cap_group']}`")
        #st.markdown(f"- **Group Capability:** `{row['group_capability']}`")
        #st.markdown(f"- **👤 Head of Profession:** `{row['global_sme'] or 'TBC'}`")
        #st.markdown("**👥 Divisional Contacts:**")
        #st.markdown(f"  - Environment: `{row['sme_env'] or 'TBC'}`")
        #st.markdown(f"  - Energy: `{row['sme_energy'] or 'TBC'}`")
        #st.markdown(f"  - D&AS: `{row['sme_das'] or 'TBC'}`")
        #st.markdown(f"  - TC&I: `{row['sme_tci'] or 'TBC'}`")
        #st.markdown(f"  - APAC: `{row['sme_apac'] or 'TBC'}`")
        #st.markdown("---")

# --- US Reachback Page ---

elif st.session_state.page == "US Reachback":
    st.title("US Reachback Capabilities")

   # (keep option for later date) us_capabilities = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])

    default_path = "us_capability_groups.xlsx"
    
    if os.path.exists(default_path):
        df = pd.read_excel(default_path, engine='openpyxl')

        if all(col in df.columns for col in ['Capability_Groups', 'Capabilities', 'Contact', 'Email']):
            st.write("### Capability Groups ")
        
            groupings = df['Capability_Groups'].dropna().unique()

            for grouping in sorted(groupings):
                with st.expander(grouping):
                    grouping_df = df[df['Capability_Groups'] == grouping][['Capabilities', 'Contact', 'Email']].reset_index(drop=True)
                    st.dataframe(grouping_df, hide_index=True)
        else:
            st.error("The Excel file must contain the columns: Capability_Groups, Capabilities, Contact, and Email.")

    else:
        st.warning("Default Excel file not found.")


# --- Dashboard Page ---
elif st.session_state.page == "Dashboard":
    st.title("📊 Resources Dashboard")
    
    data_set = "capacity_data.xlsx"
    if os.path.exists(data_set):
        df = pd.read_excel(data_set, engine='openpyxl')

        # Set up layout
        st.write("### Overview Visualisations")

        # Bar Chart: Distribution by Division
        st.subheader("Distribution by Division")
        division_counts = df['Division'].value_counts().reset_index()
        division_counts.columns = ['Division', 'Count']
        bar_chart_division = alt.Chart(division_counts).mark_bar().encode(
            x='Count:Q',
            y=alt.Y('Division:N', sort='-x')
        ).configure_axis(
            labelFontSize=12,
            titleFontSize=14,
            labelLimit=170
        )
        st.altair_chart(bar_chart_division, use_container_width=True)

        
        donut_chart = alt.Chart(division_counts).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Division", type="nominal"),
            tooltip=["Division", "Count"]
        ).properties(
            title="Distribution by Division"
        )
        st.altair_chart(donut_chart, use_container_width=True)
        

        # Donut Chart: Distribution by Country
        st.subheader("Distribution by Country")
        
        
        #extra code for map chart
        country_counts = df.groupby('Country').size().reset_index(name='count')
        country_counts['color'] = 1
        fig = px.choropleth(country_counts,
                            locations="Country",
                            locationmode="country names",
                            color="count",
                            projection="robinson",
                            title="Distribution by Country",
                            color_continuous_scale=[[0, 'white'], [1, '#39B54A']],
                            range_color=(0,1))

        fig.update_layout(coloraxis_showscale=False)

        st.plotly_chart(fig)

        
        selected_country = st.selectbox("Select a country to view city-level data", sorted(df['Country'].unique()))

        filtered_data = df[df['Country'] == selected_country]

        city_counts = filtered_data.groupby(['Location', 'Latitude', 'Longitude']).size().reset_index(name='count')
        city_counts.columns = ['City', 'Latitude', 'Longitude', 'count']

        center_lat = city_counts['Latitude'].mean()
        center_lon = city_counts['Longitude'].mean()

        city_counts['log_count'] = np.log1p(city_counts['count'])    # log(1 + count)
        min_size = 3
        city_counts['scaled_size'] = city_counts['log_count'] + min_size

        

        fig_city =px.scatter_geo(city_counts,
                                 lat='Latitude',
                                 lon='Longitude',
                                 size='scaled_size',
                                 hover_name="City",
                                 hover_data={'count': True, 'Latitude': False, 'Longitude': False, 'scaled_size': False},
                                 projection="robinson",
                                 title=f"City-Level Distribution in {selected_country}")

        fig_city.update_geos(
            center={"lat": center_lat, "lon": center_lon},
            projection_scale=9,
            showcountries=True,
            showland=True,
            landcolor="LightGreen"
        )
        
       # st.subheader(f"City-Level Distribution in {selected_country}")
        st.plotly_chart(fig_city)
        
       

        # Bar Chart: Top 10 Locations
        st.subheader("Top 10 Locations")
        top_locations = df['Location'].value_counts().head(10).reset_index()
        top_locations.columns = ['Location', 'Count']
        bar_chart_locations = alt.Chart(top_locations).mark_bar().encode(
            x='Count:Q',
            y=alt.Y('Location:N', sort='-x')
        )
        st.altair_chart(bar_chart_locations, use_container_width=True)

        # Bar Chart: Top 10 Job Families
        st.subheader("Top 10 Job Families")
        top_jobs = df['Job family'].value_counts().head(10).reset_index()
        top_jobs.columns = ['Job family', 'Count']
        bar_chart_jobs = alt.Chart(top_jobs).mark_bar().encode(
            x='Count:Q',
            y=alt.Y('Job family:N', sort='-x')
        ).configure_axis(
            labelFontSize=12,
            titleFontSize=14,
            labelLimit=170
        )
        st.altair_chart(bar_chart_jobs, use_container_width=True)

    else:
        st.warning("The data file was not found.")

    
# --- Feedback Page ---
elif st.session_state.page == "Feedback":
    st.title("📝 Feedback Form")
    
# Use a unique variable name for the feedback database connectio
    feedback_conn = sqlite3.connect("feedback.db", check_same_thread=False)
    feedback_cursor = feedback_conn.cursor()

# Create table if it doesn't exist
    feedback_cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            rating INTEGER,
            choice TEXT,
            question TEXT,
            success TEXT,
            suggestion TEXT,
            comments TEXT,
            submitted_at TEXT
        )
    """)

    feedback_conn.commit()

# Feedback form
    with st.form("feedback_form"):
        name = st.text_input("Your Name")
        email = st.text_input("Your Email")
        st.markdown("<p style='font-size: 14px; font-weight: 400;'>Overall, how would you rate your experience using CapabilityConnect?</p>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 8, 1])
        with col1:
            st.markdown("<p style='font-size: 14px; font-weight: 400;'>Poor</p>", unsafe_allow_html=True)
        with col2:
            pass
        with col3:
            st.markdown("<p style='text-align: right; font-size: 14px; font-weight: 400;'>Great</p>", unsafe_allow_html=True)
        rating = st.slider("", 1, 5, 3, label_visibility="collapsed")
        choice = st.selectbox("What kind of feedback do you wish to submit?", ["Report a fault or issue", "Make a suggestion"])
        question = st.text_input("What were you searching for? (If leaving a suggestion for the app, please ignore this question and the next)")
        success = st.radio("Did you find what you were looking for?", ["Yes", "No"])
        suggestion = st.text_area("Please enter your suggestions for how the app can be improved below")
        comments = st.text_area("Additional Comments")
        submitted = st.form_submit_button("Submit Feedback")
        
        if submitted:
            timestamp = datetime.now().isoformat()
            feedback_cursor.execute("INSERT INTO feedback (name, email, rating, choice, question, success, suggestion, comments, submitted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    (name, email, rating, choice, question, success, suggestion, comments, timestamp))
            feedback_conn.commit()
            st.success("Thank you for your feedback! 🎉")

# Download feedback as CSV
    if st.session_state.role == "admin":
        st.markdown("### 📥 Download Feedback")
        if st.button("Download CSV"):
            df = pd.read_sql_query("SELECT * FROM feedback", feedback_conn)
            csv = df.to_csv(index=False)
            st.download_button("Click to Download", csv, "feedback.csv", "text/csv")
    else :
        pass
        



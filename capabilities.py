import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import altair as alt
from datetime import datetime
import os

# --- Password Hashes ---
VIEWER_PASSWORD = "a031faaa259fb838388c52358bd295b06cefaf784df98000e9cff353c27fda4f" # 'amentum2025'
ADMIN_PASSWORD = "0e89f223e226ae63268cf39152ab75722e811b89d29efb22a852f1667bd22ae0"  # 'admin2025'

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
st.sidebar.title("🧭 Navigation")


pages_admin = ["Home", "Admin", "Search", "Explorer", "US Reachback", "Dashboard", "Feedback"]
pages_user = ["Home", "Search", "Explorer", "US Reachback", "Feedback"]
pages = pages_admin if st.session_state.role == "admin" else pages_user

for p in pages:
    if st.session_state.page == p:
        st.sidebar.markdown(f"**➡️ {p}**")
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
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Search"):
            navigate("Search")
            
    with col2:
        if st.button("📚 Explorer"):
            navigate("Explorer")

    with col3:
        if st.button("💬 Feedback"):
            navigate("Feedback")
            
# --- Search Page ---
elif st.session_state.page == "Search":
    st.title("🔍 Capability Search")
    df = load_data_from_db()
    search = st.text_input("Search for a skill or competency")

    if search:
        filtered = df[
            df["skill"].str.contains(search, case=False, na=False) |
            df["competency"].str.contains(search, case=False, na=False) |
            df["key_words"].str.contains(search, case=False, na=False)
        ]


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
                    col3, col4 = st.columns(2)
                    with col3:
                        st.markdown(f"- **Capability Group:**")
                        st.markdown(f"- **Group Capability:**")
                    with col4:
                        st.button(f"`{row['cap_group']}`", key=f"cap_group_btn_{_}")
                        st.button(f"`{row['group_capability']}`", key=f"group_capability_btn_{_}")
                    st.markdown(f"- **👤 Head of Profession:** `{row['global_sme'] or 'TBC'}`")
                    st.markdown("- **👥 Divisional Contacts:**")
                    st.markdown(f"  - Environment: `{row['sme_env'] or 'TBC'}`")
                    st.markdown(f"  - Energy: `{row['sme_energy'] or 'TBC'}`")
                    st.markdown(f"  - D&AS: `{row['sme_das'] or 'TBC'}`")
                    st.markdown(f"  - TC&I: `{row['sme_tci'] or 'TBC'}`")
                    st.markdown(f"  - APAC: `{row['sme_apac'] or 'TBC'}`")
                    st.markdown("---")

# --- Explorer Page ---
elif st.session_state.page == "Explorer":
    st.title("🗂️ Capability Explorer")
    df = load_data_from_db()
    df = df.dropna(how='all')
    
    if df.empty:
        st.warning("No data found. Admins must upload a capability file.")
        st.stop()

    domain = st.selectbox("Select a discipline", sorted(df["domain"].dropna().unique()))
    filtered = df[df["domain"].str.strip().str.lower() == domain.strip().lower()]

    st.markdown(f"**🔎 {len(filtered)} result(s) found.**") #Shows number of search results

    for _, row in filtered.iterrows():
        st.markdown(f"### 🧠 {row['skill']}")
        st.markdown(f"- **Competency:** {row['competency']}")
        st.markdown(f"- **Description:** {row['description'] or '*No description*'}")
        st.markdown(f"- **Capability Group:** `{row['cap_group']}`")
        st.markdown(f"- **Group Capability:** `{row['group_capability']}`")
        st.markdown(f"- **👤 Head of Profession:** `{row['global_sme'] or 'TBC'}`")
        st.markdown("**👥 Divisional Contacts:**")
        st.markdown(f"  - Environment: `{row['sme_env'] or 'TBC'}`")
        st.markdown(f"  - Energy: `{row['sme_energy'] or 'TBC'}`")
        st.markdown(f"  - D&AS: `{row['sme_das'] or 'TBC'}`")
        st.markdown(f"  - TC&I: `{row['sme_tci'] or 'TBC'}`")
        st.markdown(f"  - APAC: `{row['sme_apac'] or 'TBC'}`")
        st.markdown("---")
# --- US Reachback Page ---

elif st.session_state.page == "US Reachback":
    st.title("US Reachback page")

   # (keep option for later date) us_capabilities = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])

    default_path = "us_capability_groups.xlsx"

    #st.write(f"Looking for file at: {default_path}")
    #st.write(f"Current working directory: {os.getcwd()}")
    
    if os.path.exists(default_path):
        df = pd.read_excel(default_path)
        st.write("### Preview of Excel Data")
        st.dataframe(df)
    else:
        st.warning("Default Excel file not found.")


# --- Dashboard Page ---
elif st.session_state.page == "Dashboard":
    st.title("📊 Capability Dashboard")
    df = load_data_from_db()
    if df.empty:
        st.warning("The database is currently empty. Please upload data in the Admin panel.")
        st.stop()

    df["has_sme"] = df["global_sme"].apply(lambda x: isinstance(x, str) and x.strip().lower() != "nan" and x.strip() != "")

    st.subheader("SME Assignment Overview")
    sme_summary = df["has_sme"].value_counts().rename({True: "Assigned", False: "Unassigned"}).reset_index()
    sme_summary.columns = ["Status", "Count"]

    if not sme_summary.empty:
        chart = alt.Chart(sme_summary).mark_bar().encode(x="Status", y="Count", color="Status")
        st.altair_chart(chart, use_container_width=True)

    st.subheader("Skills per Discipline")
    domain_counts = df["domain"].value_counts().reset_index()
    domain_counts.columns = ["Domain", "Skill Count"]
    if not domain_counts.empty:
        st.bar_chart(domain_counts.set_index("Domain"))

    st.subheader("Top Capability Groups")
    top_groups = df["cap_group"].value_counts().dropna().head(10).reset_index()
    top_groups.columns = ["Capability Group", "Count"]
    st.dataframe(top_groups)

    st.subheader("Capabilities Missing SME")
    required_cols = {"domain", "competency", "skill", "global_sme"}
    if required_cols.issubset(df.columns):
        st.dataframe(df[~df["has_sme"]][["domain", "competency", "skill", "global_sme"]])
    else:
        st.warning("Expected columns not found in the data.")

    st.download_button(
        label="📥 Download All Capabilities (CSV)",
        data=df.to_csv(index=False),
        file_name="amentum_capabilities.csv"
    )
    
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
            comments TEXT,
            submitted_at TEXT
        )
    """)

    feedback_conn.commit()

# Feedback form
    with st.form("feedback_form"):
        name = st.text_input("Your Name")
        email = st.text_input("Your Email")
        rating = st.slider("How would you rate the app?", 1, 5, 3)
        comments = st.text_area("Additional Comments")
        submitted = st.form_submit_button("Submit Feedback")
        
        if submitted:
            timestamp = datetime.now().isoformat()
            feedback_cursor.execute("INSERT INTO feedback (name, email, rating, comments, submitted_at) VALUES (?, ?, ?, ?, ?)",
                                    (name, email, rating, comments, timestamp))
            feedback_conn.commit()
            st.success("Thank you for your feedback! 🎉")

# Download feedback as CSV
    st.markdown("### 📥 Download Feedback")
    if st.button("Download CSV"):
        df = pd.read_sql_query("SELECT * FROM feedback", feedback_conn)
        csv = df.to_csv(index=False)
        st.download_button("Click to Download", csv, "feedback.csv", "text/csv")



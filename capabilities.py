import streamlit as st
import pandas as pd
import numpy as np
import hashlib
import altair as alt

# --- Secure login with hashed password ---
HASHED_PASSWORD = "a031faaa259fb838388c52358bd295b06cefaf784df98000e9cff353c27fda4f"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Amentum Capability Search Login")
    pwd = st.text_input("Enter password", type="password")
    if hashlib.sha256(pwd.encode()).hexdigest() == HASHED_PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    elif pwd:
        st.error("Incorrect password.")
    st.stop()

# --- Load Excel from GitHub ---
@st.cache_data
def load_all_domains():
    url = "https://raw.githubusercontent.com/DR-amentum/capabilities/6715bd159442872f51c0152f8b35134585a0a5fb/Amentum%20Skills%20Framework%20-%20HoP%20Version.xlsx"
    xls = pd.ExcelFile(url, engine="openpyxl")
    exclude = ["Info", "Level Definitions", "Definitions", "Sheet2"]
    sheets = [s for s in xls.sheet_names if s not in exclude]
    all_data = []

    for sheet in sheets:
        try:
            df = xls.parse(sheet, skiprows=2)
            df.columns = [str(c).strip().replace('\xa0', ' ') for c in df.columns]
            df["Domain"] = sheet
            all_data.append(df)
        except Exception:
            continue

    combined = pd.concat(all_data, ignore_index=True)
    combined.columns = [c.strip() for c in combined.columns]
    return combined

df = load_all_domains()

# --- SME Column Setup ---
global_sme_col = next((col for col in df.columns if "Lead Contact" in col and "Division" not in col), None)
sme_div_cols = {
    "Environment": "Lead Contact in Division (SME, Team Lead, Head of etc)",
    "Energy": "Unnamed: 17",
    "D&AS": "Unnamed: 18",
    "TC&I": "Unnamed: 19",
    "APAC": "Unnamed: 20"
}

# --- Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Capability Explorer", "Dashboard"])

# --- Page 1: Explorer ---
if page == "Capability Explorer":
    st.title("🔍 Capability Explorer")

    search = st.text_input("Search for a Skill or Competency")

    with st.expander("🔧 Filter Explorer"):
        selected_domains = st.multiselect("Filter by Domain", sorted(df["Domain"].dropna().unique()))
        show_only_unassigned = st.checkbox("Show only skills without SME", value=False)

    filtered = df.copy()

    if search:
        filtered = filtered[
            df["Skill"].astype(str).str.contains(search, case=False, na=False) |
            df["Competency"].astype(str).str.contains(search, case=False, na=False)
        ]

    if selected_domains:
        filtered = filtered[filtered["Domain"].isin(selected_domains)]

    if show_only_unassigned:
        filtered = filtered[df[global_sme_col].isna() | (df[global_sme_col].astype(str).str.lower() == "nan")]

    if filtered.empty:
        st.warning("No matching capabilities found.")
    else:
        grouped = filtered.groupby("Domain")
        for domain, group in grouped:
            st.markdown(f"## 🏷️ {domain}")
            for _, row in group.iterrows():
                skill = str(row.get("Skill", "")).strip()
                competency = str(row.get("Competency", "")).strip()
                description = str(row.get("Description", "")).strip()
                cap_group = str(row.get("Unnamed: 8", "")).strip()
                group_cap = str(row.get("Unnamed: 9", "")).strip()
                sme_global = str(row.get(global_sme_col, "")).strip() if global_sme_col else "TBC"

                st.markdown("---")
                st.markdown(f"### 🧠 **{skill or competency}**")
                st.markdown(f"**Competency:** {competency}")
                st.markdown(f"**Description:** {description or '*No description available*'}")
                st.markdown(f"**Capability Group:** `{cap_group}`")
                st.markdown(f"**Group Capability:** `{group_cap}`")
                st.markdown(f"**👤 Global SME:** `{sme_global if sme_global and sme_global.lower() != 'nan' else 'TBC'}`")
                st.markdown("**👥 Lead Contacts by Division:**")
                for label, col in sme_div_cols.items():
                    contact = str(row.get(col, "")).strip()
                    contact_display = contact if contact and contact.lower() != "nan" else "TBC"
                    st.markdown(f"- {label}: `{contact_display}`")

# --- Page 2: Dashboard ---
elif page == "Dashboard":
    st.title("📊 Capability Dashboard")

    df["Has SME"] = df[global_sme_col].apply(lambda x: False if pd.isna(x) or str(x).strip().lower() == "nan" else True)

    st.subheader("SME Assignment Overview")
    sme_counts = df["Has SME"].value_counts().rename({True: "Assigned", False: "Unassigned"}).reset_index()
    sme_counts.columns = ["Status", "Count"]
    chart = alt.Chart(sme_counts).mark_bar().encode(
        x="Status",
        y="Count",
        color="Status"
    )
    st.altair_chart(chart, use_container_width=True)

    st.subheader("Skills per Domain")
    domain_counts = df["Domain"].value_counts().reset_index()
    domain_counts.columns = ["Domain", "Skills"]
    st.bar_chart(domain_counts.set_index("Domain"))

    st.subheader("Top Capability Groups")
    cap_counts = df["Unnamed: 8"].value_counts().head(10).reset_index()
    cap_counts.columns = ["Capability Group", "Count"]
    st.dataframe(cap_counts)

    st.subheader("Capabilities Missing SME")
    missing = df[~df["Has SME"]].copy()
    st.dataframe(missing[["Domain", "Competency", "Skill", global_sme_col]].rename(columns={global_sme_col: "SME"}))

    st.download_button("📥 Download All Capabilities (CSV)", df.to_csv(index=False), file_name="all_capabilities.csv")
    

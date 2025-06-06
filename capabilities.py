import streamlit as st
import pandas as pd
import hashlib

# --- 🔐 Simple Password Protection ---
HASHED_PASSWORD = "a031faaa259fb838388c52358bd295b06cefaf784df98000e9cff353c27fda4f"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Enter Password to Access Capability Search")
    pwd = st.text_input("Password", type="password")
    hashed_input = hashlib.sha256(pwd.encode()).hexdigest()
    if hashed_input == HASHED_PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    elif pwd:
        st.error("❌ Incorrect password.")
    st.stop()

# --- 📥 Load and clean all domain sheets ---
@st.cache_data
def load_all_domains():
    xls = pd.ExcelFile("Amentum Skills Framework - HoP Version.xlsx")
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

# --- 🚀 App UI ---
st.title("🔍 Amentum Capability Search")

# Load data
df = load_all_domains()

# Detect global SME and division SME columns
global_sme_col = next((col for col in df.columns if "Lead Contact" in col and "Division" not in col), None)
sme_div_cols = {
    "Environment": "Lead Contact in Division (SME, Team Lead, Head of etc)",
    "Energy": "Unnamed: 17",
    "D&AS": "Unnamed: 18",
    "TC&I": "Unnamed: 19",
    "APAC": "Unnamed: 20"
}

# Search box
search = st.text_input("Search for a Skill or Competency")

if search:
    mask = df.apply(lambda row: search.lower() in str(row.get("Skill", "")).lower()
                                 or search.lower() in str(row.get("Competency", "")).lower(), axis=1)
    results = df[mask]

    if results.empty:
        st.warning("No matching capabilities found.")
    else:
        st.write(f"### {len(results)} result(s) found for '{search}'")

        grouped = results.groupby("Domain")

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

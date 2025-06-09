# 🔍 Amentum Capability Search Tool (Admin Enabled)

A password-protected Streamlit app to search, explore, edit, and manage engineering capabilities across all domains at Amentum. Includes full admin upload, dashboard insights, and divisional SME tracking.

---

## 1. ⚙️ Set Up Your Environment (Anaconda)

**Step 1:** Create and activate a new conda environment

```
conda create -n capability_env python=3.10
conda activate capability_env
```

---

## 2. 📦 Install Dependencies

**Step 2:** Install required packages

```
pip install -r requirements.txt
```

---

## 3. 📁 File Structure

Your folder should contain:

- `capabilities.py` – the main Streamlit app  
- `requirements.txt` – Python package list  
- `capabilities.db` – created automatically after first upload  
- (Optional) Excel upload: `Amentum Skills Framework - HoP Version.xlsx`

---

## 4. 🔐 Launch the App (Admin or Viewer Login)

**Step 3:** Run the app

```
streamlit run capabilities.py
```

Access in browser: [http://localhost:8501](http://localhost:8501)

- Admin login allows upload and editing
- Viewer login allows searching and browsing only

---

## 5. 👥 Roles & Features

### Viewer Mode
- 🔍 Search by Skill or Competency
- 🗂️ Explore by Domain
- 📊 Dashboard visualisations
- 👤 SME contacts by division:
  - Global
  - Environment
  - Energy
  - D&AS
  - TC&I
  - APAC

### Admin Mode
- 📤 Upload a new Excel framework file (clears old data)
- 🛠 Search and edit individual capability cards
- 📝 Edit all card fields inline in the UI
- ✅ Edits save directly to SQLite database

---

## 6. 🧾 Updating the Framework File (Admin Only)

1. Login as admin
2. Upload a new Excel file
3. Data will be parsed, old data cleared, and saved to database

No restart required – changes reflect instantly.

---

## 7. 🛠 Optional Commands

To regenerate the `requirements.txt` file:

```
pip freeze > requirements.txt
```

To delete the local database (e.g. reset):

```
rm capabilities.db
```

---

## 📄 License

Internal tool – property of Amentum CMS. Not for public distribution.

# 🔍 Amentum Capability Search Tool

A password-protected Streamlit app to search capabilities across all engineering domains at Amentum. Displays detailed descriptions, capability groupings, and SME contacts by division.

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

*Make sure you're in the same directory as `requirements.txt`.*

---

## 3. 📁 File Structure

Your folder should contain:

- `capabilities.py` – the main Streamlit app  
- `Amentum Skills Framework - HoP Version.xlsx` – the capability data  
- `requirements.txt` – the list of required Python packages

---

## 4. 🔐 Launch the App (Password Protected)

**Step 3:** Run the app

```
streamlit run capabilities.py
```

The app will open in your browser at:

[http://localhost:8501](http://localhost:8501)


---

## 5. 🔍 Using the App

- Search by **Skill** or **Competency**
- Results are grouped by **Domain** (e.g. Physics, HVAC, EC&I)
- Each result shows:
  - Description
  - Capability Group
  - Group Capability
  - SME Contacts:
    - Global
    - Environment
    - Energy
    - D&AS
    - TC&I
    - APAC

---

## 6. 🧾 Updating the Framework File

To update data:

1. Open `Amentum Skills Framework - HoP Version.xlsx`
2. Modify or add capabilities under the correct sheet (e.g. "Physics")
3. Save the file
4. Restart or refresh the app

The changes will be automatically reflected.

---

## 7. 🛠 Optional Commands

To regenerate the `requirements.txt` file (if needed):

```
pip freeze > requirements.txt
```

---

## 📄 License

Internal tool – property of Amentum CMS. Not for public distribution.

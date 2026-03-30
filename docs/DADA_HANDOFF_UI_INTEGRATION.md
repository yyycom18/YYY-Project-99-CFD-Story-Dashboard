# 📘 HANDOFF TO DADA: DASHBOARD GUIDE UI INTEGRATION

**From:** Chris (Code Review Agent)  
**To:** Dada (Development Agent)  
**Date:** 2026-03-11  
**Status:** READY FOR IMPLEMENTATION

---

## OVERVIEW

You need to integrate a "Dashboard Guide (Manual)" section into the sidebar navigation.

**What's included:**
- 4 comprehensive markdown documentation files (in `/docs` folder)
- UI integration instructions (this document)
- File structure (already created)
- No code changes to engine (UI only)

**Time estimate:** 30–45 minutes

---

## 📁 FILE STRUCTURE (ALREADY CREATED)

Location: `/docs` folder inside project

```
YYY-Project-99-CFD-Story-Dashboard/
├── docs/
│   ├── 00_DASHBOARD_GUIDE.md          [Main guide]
│   ├── 01_MARKET_SCANNER.md           [Scanner details]
│   ├── 02_DATA_LOADING_LOGIC.md       [Technical flow]
│   └── 03_SIGNAL_BIAS_EXPLAINED.md    [Concepts]
│
└── app.py                              [Modify for navigation]
```

---

## ✅ IMPLEMENTATION STEPS

### Step 1: Add Navigation to Sidebar

**File:** `app.py`

**Location:** After title/caption (~line 234–236), before render_scanner()

**Add this code:**

```python
# Dashboard navigation
def render_guide_page():
    """Render Dashboard Guide from markdown files."""
    # Load main guide
    with open("docs/00_DASHBOARD_GUIDE.md", "r", encoding="utf-8") as f:
        guide_content = f.read()
    
    # Render with sidebar navigation to sub-sections
    st.markdown(guide_content)
    
    # Add navigation links
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📊 Market Scanner", use_container_width=True):
            st.session_state["guide_page"] = "market_scanner"
    with col2:
        if st.button("🔄 Data Loading", use_container_width=True):
            st.session_state["guide_page"] = "data_loading"
    with col3:
        if st.button("🎯 Signal & Bias", use_container_width=True):
            st.session_state["guide_page"] = "signal_bias"
    with col4:
        if st.button("← Main Guide", use_container_width=True):
            st.session_state["guide_page"] = "main"

# Initialize session state for guide page
if "guide_page" not in st.session_state:
    st.session_state["guide_page"] = "main"
```

**Add after main title (line ~235):**

```python
# Main navigation
page = st.sidebar.selectbox(
    "📍 Navigation",
    ["📊 Market Scanner", "📈 Asset Story", "📘 Dashboard Guide"]
)
```

---

### Step 2: Add Guide Page Routing

**File:** `app.py`

**Location:** After navigation selectbox, before existing render_scanner() call (~line 280)

**Replace the existing main structure with:**

```python
# Route to appropriate page
if page == "📊 Market Scanner":
    render_scanner()
    
elif page == "📈 Asset Story":
    render_asset_dashboard()
    
elif page == "📘 Dashboard Guide":
    # Load and render appropriate guide page
    if st.session_state.get("guide_page") == "market_scanner":
        with open("docs/01_MARKET_SCANNER.md", "r", encoding="utf-8") as f:
            st.markdown(f.read())
    elif st.session_state.get("guide_page") == "data_loading":
        with open("docs/02_DATA_LOADING_LOGIC.md", "r", encoding="utf-8") as f:
            st.markdown(f.read())
    elif st.session_state.get("guide_page") == "signal_bias":
        with open("docs/03_SIGNAL_BIAS_EXPLAINED.md", "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        # Main guide (default)
        with open("docs/00_DASHBOARD_GUIDE.md", "r", encoding="utf-8") as f:
            st.markdown(f.read())
        
        # Add navigation buttons at bottom
        st.divider()
        st.subheader("📚 Documentation Sections")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 Market Scanner Guide", use_container_width=True, key="nav_scanner"):
                st.session_state["guide_page"] = "market_scanner"
                st.rerun()
        
        with col2:
            if st.button("🔄 Data Loading Logic", use_container_width=True, key="nav_data"):
                st.session_state["guide_page"] = "data_loading"
                st.rerun()
        
        with col3:
            if st.button("🎯 Signal & Bias", use_container_width=True, key="nav_signal"):
                st.session_state["guide_page"] = "signal_bias"
                st.rerun()
        
        with col4:
            if st.button("← Back to Main", use_container_width=True, key="nav_main"):
                st.session_state["guide_page"] = "main"
                st.rerun()
```

---

### Step 3: Handle File Paths

**Important:** Files are accessed as `docs/00_DASHBOARD_GUIDE.md`

**For this to work:**
- Run dashboard from project root: `cd YYY-Project-99-CFD-Story-Dashboard && streamlit run app.py`
- Files in `/docs` subfolder will be found automatically

**If file not found error:**
```python
# Add this debugging line to check path
import os
print(f"Current working directory: {os.getcwd()}")
print(f"Docs folder exists: {os.path.exists('docs')}")
print(f"Files in docs: {os.listdir('docs')}")
```

---

### Step 4: Add Error Handling

**File:** `app.py`

**In the guide page routing section, wrap file reads:**

```python
try:
    with open("docs/00_DASHBOARD_GUIDE.md", "r", encoding="utf-8") as f:
        st.markdown(f.read())
except FileNotFoundError:
    st.error("📚 Guide file not found. Ensure docs folder exists in project root.")
    st.info("Project structure:\n```\nYYY-Project-99-CFD-Story-Dashboard/\n├── docs/\n│   ├── 00_DASHBOARD_GUIDE.md\n│   ├── 01_MARKET_SCANNER.md\n│   ├── 02_DATA_LOADING_LOGIC.md\n│   └── 03_SIGNAL_BIAS_EXPLAINED.md\n└── app.py\n```")
```

---

## 🧪 TESTING CHECKLIST

### Before Submitting PR

- [ ] Sidebar shows: "📊 Market Scanner", "📈 Asset Story", "📘 Dashboard Guide"
- [ ] Clicking "📘 Dashboard Guide" shows main guide page
- [ ] Navigation buttons at bottom work correctly:
  - [ ] "📊 Market Scanner Guide" button → loads 01_MARKET_SCANNER.md
  - [ ] "🔄 Data Loading Logic" button → loads 02_DATA_LOADING_LOGIC.md
  - [ ] "🎯 Signal & Bias" button → loads 03_SIGNAL_BIAS_EXPLAINED.md
  - [ ] "← Back to Main" button → returns to main guide
- [ ] All markdown renders correctly (headings, lists, tables)
- [ ] Links in guide work (internal navigation)
- [ ] No layout issues (text readable, not overlapping)
- [ ] Mobile responsive (sidebar still accessible on mobile)

### Local Testing

```bash
cd YYY-Project-99-CFD-Story-Dashboard
streamlit run app.py
```

1. Check sidebar navigation loads
2. Click "📘 Dashboard Guide"
3. Verify main guide displays
4. Click each navigation button
5. Verify each section loads correctly
6. Check no errors in terminal

---

## 📋 CODE CHANGES SUMMARY

### Modified File: `app.py`

**Changes:**
1. Add sidebar navigation selectbox (~3 lines)
2. Add session state for guide page tracking (~2 lines)
3. Add main routing structure (~50 lines for if/elif)
4. Add guide page rendering with file loading (~40 lines)
5. Add navigation buttons for sub-sections (~30 lines)

**Total:** ~125 lines added (can be optimized into helper function if needed)

**No changes to:**
- ❌ Engine logic
- ❌ Data loading
- ❌ Caching
- ❌ Existing scanner/asset views

---

## 🚀 OPTIMIZATION (OPTIONAL)

### Option 1: Cache Markdown Reads

```python
@st.cache_data
def load_guide_content(filename):
    """Load markdown file once and cache."""
    try:
        with open(f"docs/{filename}", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: {filename} not found"

# Usage:
guide_text = load_guide_content("00_DASHBOARD_GUIDE.md")
st.markdown(guide_text)
```

**Benefit:** Guides load instantly on repeat visits

---

### Option 2: Extract to Helper Function

```python
def render_guide_section(section_name):
    """Load and render guide section."""
    guide_files = {
        "main": "00_DASHBOARD_GUIDE.md",
        "market_scanner": "01_MARKET_SCANNER.md",
        "data_loading": "02_DATA_LOADING_LOGIC.md",
        "signal_bias": "03_SIGNAL_BIAS_EXPLAINED.md",
    }
    
    filename = guide_files.get(section_name, "00_DASHBOARD_GUIDE.md")
    with open(f"docs/{filename}", "r", encoding="utf-8") as f:
        st.markdown(f.read())

# Usage:
render_guide_section(st.session_state.get("guide_page", "main"))
```

**Benefit:** Cleaner code, easier to maintain

---

## 📝 PR DESCRIPTION TEMPLATE

```markdown
## Feature: Dashboard Guide Integration

### Changes
- ✅ Added "📘 Dashboard Guide" to sidebar navigation
- ✅ Created 4 comprehensive markdown guides in `/docs` folder
- ✅ Integrated file loading and rendering in app.py
- ✅ Added internal navigation buttons between guide sections
- ✅ Added error handling for missing files

### File Structure
```
docs/
├── 00_DASHBOARD_GUIDE.md      (Main guide)
├── 01_MARKET_SCANNER.md       (Scanner details)
├── 02_DATA_LOADING_LOGIC.md   (Technical flow)
└── 03_SIGNAL_BIAS_EXPLAINED.md (Concept definitions)
```

### Testing
- ✅ Sidebar navigation working
- ✅ All guide sections load correctly
- ✅ Navigation buttons tested
- ✅ Markdown renders properly
- ✅ No performance impact
- ✅ Mobile responsive

### Screenshots
[Add before/after screenshots here]

### Notes
- No engine logic changes
- No performance impact
- Documentation is cached for fast loading
- All files stored in project folder (not external)
```

---

## ⚠️ COMMON ISSUES & FIXES

### Issue: FileNotFoundError

**Error:** `FileNotFoundError: docs/00_DASHBOARD_GUIDE.md`

**Cause:** App not running from project root

**Fix:**
```bash
# Correct
cd YYY-Project-99-CFD-Story-Dashboard
streamlit run app.py

# Wrong
cd C:\Users\user\Desktop\Cursor
streamlit run YYY-Project-99-CFD-Story-Dashboard/app.py
```

---

### Issue: Markdown Not Rendering

**Symptom:** Raw markdown text visible instead of formatted

**Fix:** Use `st.markdown()` not `st.write()`:
```python
# Correct
st.markdown(content)

# Wrong
st.write(content)  # Shows raw text
```

---

### Issue: Session State Not Working

**Symptom:** Navigation buttons don't change page

**Fix:** Ensure `st.rerun()` called after button click:
```python
if st.button("Next", key="btn_next"):
    st.session_state["guide_page"] = "next"
    st.rerun()  # ← Must call rerun
```

---

### Issue: Sidebar Buttons Not Appearing

**Symptom:** Navigation buttons only show in main area

**Note:** This is OK! Sidebar is for page selection, main area is for navigation within pages.

---

## 📞 QUESTIONS?

**For file locations:** All `docs/` files are in `YYY-Project-99-CFD-Story-Dashboard/docs/`

**For syntax:** Use standard Streamlit markdown and session state patterns

**For performance:** Guides are lightweight (markdown text only), no performance impact expected

---

## ✅ FINAL CHECKLIST

Before opening PR:

- [ ] All 4 markdown files exist in `/docs`
- [ ] Sidebar navigation selectbox added
- [ ] Session state initialized for guide page
- [ ] Guide routing logic added
- [ ] Navigation buttons implemented
- [ ] Error handling for missing files
- [ ] All sections tested locally
- [ ] No console errors
- [ ] PR description filled out
- [ ] Screenshots included

---

**Ready to implement? Let's go! 🚀**


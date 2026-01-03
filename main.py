import streamlit as st
from agent import fact_checker_app

# --- UI Configuration ---
st.set_page_config(
    page_title="Forensic AI Shield 2026",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Forensic AI Hallucination & Citation Detector")
st.info("System Date: January 4, 2026 | Mode: Hard-Core Forensic Audit")

# --- Layout ---
col1, col2 = st.columns([1, 1])

with col1:
    user_input = st.text_area(
        "Paste Citations or Claims to Verify:",
        placeholder="Example: Smith, J. (2025). AI reaches a ceiling...",
        height=400
    )
    
    run_button = st.button("🚀 Run Forensic Audit", use_container_width=True)

with col2:
    if run_button and user_input:
        with st.status("🕵️ Agent Investigation in Progress...", expanded=True) as status:
            st.write("🔍 Identifying unique claims and titles...")
            # Execute the LangGraph workflow
            output = fact_checker_app.invoke({"query": user_input})
            
            st.write("🌐 Scraping academic and news databases...")
            st.write("⚖️ Adjudicating evidence against 2026 timeline...")
            status.update(label="Audit Complete!", state="complete")
        
        st.subheader("Final Forensic Report")
        st.markdown(output["verdict"])
        
        with st.expander("View Ground-Truth Evidence Found"):
            st.write(output["research"])
    elif run_button:
        st.error("Please provide input text first.")

# --- Sidebar for Context ---
st.sidebar.title("System Info")
st.sidebar.markdown("""
**How it works:**
1. **Planner:** Deconstructs text into searchable queries.
2. **Researcher:** Cross-references DuckDuckGo, Academic snippets, and DOIs.
3. **Adjudicator:** Compares findings to known history as of Jan 2026.
""")
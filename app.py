import streamlit as st
import pandas as pd
import io
from datetime import date

from database_pg import (
    init_db,
    insert_email,
    search_emails,
    get_database_size_gb
)

from scraper_email import search_and_extract_emails

# ============================
# INIT DB
# ============================
init_db()

# ============================
# PAGE CONFIG
# ============================
st.set_page_config(
    page_title="Email ID Extractor — Digmar",
    layout="wide"
)

# ============================
# SIDEBAR
# ============================
st.sidebar.title("📂 Navigation")

try:
    db_size = get_database_size_gb()
    st.sidebar.info(f"🗄 Neon DB Usage: {db_size} GB / 0.5 GB")
except:
    st.sidebar.warning("⚠️ DB size unavailable")

page = st.sidebar.radio(
    "Select Option",
    ["📧 Extract Emails", "🗄 View Database"]
)

# ============================
# 📧 EXTRACT EMAILS
# ============================
if page == "📧 Extract Emails":

    st.title("📧 Email ID Extractor — Digmar")

    uploaded = st.file_uploader(
        "📂 Upload Excel (.xlsx) with **keyword** column",
        type=["xlsx"]
    )

    if uploaded:
        df = pd.read_excel(uploaded)

        if "keyword" not in df.columns:
            st.error("❌ Excel must contain a column named `keyword`")
        else:
            st.success("✔ File loaded successfully")

            if st.button("🚀 Start Email Extraction"):
                progress = st.progress(0)
                all_results = []

                keywords = df["keyword"].dropna().unique().tolist()
                total = len(keywords)

                for i, keyword in enumerate(keywords):
                    st.write(f"🔍 Searching: **{keyword}**")

                    extracted = search_and_extract_emails(keyword)

                    if not extracted:
                        st.info("No emails found")
                        progress.progress((i + 1) / total)
                        continue

                    for item in extracted:
                        email = item.get("email")
                        source = item.get("source_url")
                        website = item.get("website")
                        linkedin = item.get("linkedin")
                        facebook = item.get("facebook")

                        if not email or not source:
                            continue

                        inserted, truncated = insert_email(
                            keyword,
                            email,
                            source,
                            website,
                            linkedin,
                            facebook
                        )

                        if truncated:
                            st.warning("⚠️ DB limit reached — old data auto-cleared")

                        if inserted:
                            all_results.append({
                                "keyword": keyword,
                                "email": email,
                                "website": website,
                                "source": source,
                                "linkedin": linkedin,
                                "facebook": facebook
                            })

                    progress.progress((i + 1) / total)

                if all_results:
                    out_df = pd.DataFrame(all_results)
                    st.subheader("✅ Newly Stored Emails")
                    st.dataframe(out_df, use_container_width=True)

                    buffer = io.BytesIO()
                    out_df.to_excel(buffer, index=False)
                    buffer.seek(0)

                    st.download_button(
                        "📥 Download New Emails",
                        buffer,
                        "new_emails.xlsx"
                    )
                else:
                    st.info("ℹ️ No new emails stored (duplicates or none found)")

# ============================
# 🗄 VIEW DATABASE
# ============================
if page == "🗄 View Database":

    st.title("🗄 Search Stored Email Database")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        keyword = st.text_input("Keyword")

    with col2:
        date_from = st.date_input("From Date", value=date.today())

    with col3:
        date_to = st.date_input("To Date", value=date.today())

    with col4:
        source = st.text_input("Source URL")

    if st.button("🔍 Search"):
        df = search_emails(
            keyword=keyword,
            source=source,
            date_from=str(date_from),
            date_to=str(date_to)
        )

        if df.empty:
            st.warning("No records found")
        else:
            st.success(f"✔ {len(df)} records found")
            st.dataframe(df, use_container_width=True)

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
# INITIALIZE DATABASE
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

# Show Neon DB usage
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

    st.title("📧 Email ID Extractor — ANVIA")

    uploaded = st.file_uploader(
        "📂 Upload Excel (.xlsx) with **keyword** column",
        type=["xlsx"]
    )

    if uploaded is not None:
        df = pd.read_excel(uploaded)

        if "keyword" not in df.columns:
            st.error("❌ Excel must contain a column named **keyword**")
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
                        st.info("No email IDs found")

                    for email, source in extracted:
                        # INSERT ONLY IF NOT EXISTS (handled in DB)
                        inserted, truncated = insert_email(keyword, email, source)
                        if truncated:
                            st.warning("⚠️ Database reached storage limit. Old data was auto-cleared.")

                        if inserted:
                            all_results.append({
                                "keyword": keyword,
                                "email": email,
                                "source": source
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
                        label="📥 Download New Emails (Excel)",
                        data=buffer,
                        file_name="new_emails.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("⚠️ All extracted emails already exist in database")

# ============================
# 🗄 VIEW DATABASE
# ============================
if page == "🗄 View Database":

    st.title("🗄 Search Stored Email Database")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        keyword = st.text_input("🔎 Keyword")

    with col2:
        date_from = st.date_input("📅 From Date", value=date.today())

    with col3:
        date_to = st.date_input("📅 To Date", value=date.today())

    with col4:
        source = st.text_input("🔎 Source URL")

    if st.button("🔍 Search Database"):
        df = search_emails(
            keyword=keyword,
            source=source,
            date_from=str(date_from),
            date_to=str(date_to)
        )

        if df.empty:
            st.warning("❌ No data found")
        else:
            st.success(f"✔ Found {len(df)} records")

            df_display = df[
                ["id", "keyword", "email", "source", "created_at"]
            ]

            st.dataframe(df_display, use_container_width=True)

            buffer = io.BytesIO()
            df_display.to_excel(buffer, index=False)
            buffer.seek(0)

            st.download_button(
                label="📥 Download Filtered Data (Excel)",
                data=buffer,
                file_name="filtered_emails.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

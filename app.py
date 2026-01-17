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

# INIT DB
init_db()

st.set_page_config(
    page_title="Email ID Extractor — Digmar",
    layout="wide"
)

st.sidebar.title("📂 Navigation")

try:
    db_size = get_database_size_gb()
    st.sidebar.info(f"🗄 DB Usage: {db_size} GB / 0.5 GB")
except:
    st.sidebar.warning("DB size unavailable")

page = st.sidebar.radio("Select", ["📧 Extract Emails", "🗄 View Database"])


if page == "📧 Extract Emails":
    st.title("📧 Email Extractor")

    uploaded = st.file_uploader("Upload Excel with `keyword` column", ["xlsx"])

    if uploaded:
        df = pd.read_excel(uploaded)

        if "keyword" not in df.columns:
            st.error("Excel must contain `keyword` column")
        else:
            if st.button("🚀 Start Extraction"):
                progress = st.progress(0)
                keywords = df["keyword"].dropna().unique().tolist()
                total = len(keywords)
                results = []

                for i, keyword in enumerate(keywords):
                    st.write(f"🔍 {keyword}")
                    extracted = search_and_extract_emails(keyword)

                    for item in extracted:
                        inserted, _ = insert_email(
                            keyword,
                            item["email"],
                            item["source_url"],
                            item["website"],
                            item["linkedin"],
                            item["facebook"]
                        )

                        if inserted:
                            results.append(item)

                    progress.progress((i + 1) / total)

                if results:
                    out_df = pd.DataFrame(results)
                    st.dataframe(out_df)

                    buf = io.BytesIO()
                    out_df.to_excel(buf, index=False)
                    buf.seek(0)

                    st.download_button(
                        "📥 Download",
                        buf,
                        "emails.xlsx"
                    )
                else:
                    st.info("No new emails (duplicates or none found)")


if page == "🗄 View Database":
    st.title("🗄 Database")

    keyword = st.text_input("Keyword")
    source = st.text_input("Source URL")
    date_from = st.date_input("From", value=date.today())
    date_to = st.date_input("To", value=date.today())

    if st.button("Search"):
        df = search_emails(keyword, source, str(date_from), str(date_to))
        st.dataframe(df)

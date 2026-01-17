import psycopg2
import pandas as pd
import streamlit as st
from datetime import datetime

MAX_DB_SIZE_GB = 0.45

def get_conn():
    return psycopg2.connect(st.secrets["DATABASE_URL"])

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS extracted_emails (
            id SERIAL PRIMARY KEY,
            keyword TEXT,
            email TEXT UNIQUE,
            source TEXT,
            website TEXT,
            linkedin TEXT,
            facebook TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

def get_database_size_gb():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT pg_database_size(current_database())")
    size = cur.fetchone()[0]
    cur.close()
    conn.close()
    return round(size / (1024 ** 3), 3)

def truncate_database():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE extracted_emails RESTART IDENTITY")
    conn.commit()
    cur.close()
    conn.close()

def insert_email(keyword, email, source, website, linkedin, facebook):
    inserted = False
    truncated = False

    if get_database_size_gb() >= MAX_DB_SIZE_GB:
        truncate_database()
        truncated = True

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO extracted_emails
        (keyword, email, source, website, linkedin, facebook, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (email) DO NOTHING
        RETURNING id
    """, (keyword, email, source, website, linkedin, facebook, datetime.now()))

    if cur.fetchone():
        inserted = True

    conn.commit()
    cur.close()
    conn.close()

    return inserted, truncated

def search_emails(keyword="", source="", date_from=None, date_to=None):
    conn = get_conn()

    query = "SELECT * FROM extracted_emails WHERE 1=1"
    params = []

    if keyword:
        query += " AND keyword ILIKE %s"
        params.append(f"%{keyword}%")

    if source:
        query += " AND source ILIKE %s"
        params.append(f"%{source}%")

    if date_from:
        query += " AND created_at::date >= %s"
        params.append(date_from)

    if date_to:
        query += " AND created_at::date <= %s"
        params.append(date_to)

    query += " ORDER BY created_at DESC"

    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

import streamlit as st
import datetime
import db
import pandas as pd

TOAST_BACKGROUND_COLOR_1 = '#04B34F' # '#0E5DE3'
TOAST_BACKGROUND_COLOR_2 = "#D16C6CD1"

# Toasting
def change_green_toast_color():
    # Inject CSS to change toast background
    st.markdown(
        f"""
        <style>
        div[data-testid=stToast] {{
            background-color: {TOAST_BACKGROUND_COLOR_1}; /* Change to your desired color */
            color: white; /* Optional: change text color */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Toasting
def change_red_toast_color():
    # Inject CSS to change toast background
    st.markdown(
        f"""
        <style>
        div[data-testid=stToast] {{
            background-color: {TOAST_BACKGROUND_COLOR_2}; /* Change to your desired color */
            color: white; /* Optional: change text color */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Datetime formatting
def pretty_time(ts):
    try:
        return datetime.fromisoformat(ts).strftime("%m-%d-%y")#     %H:%M:%S")
    except:
        return ts
    
# Reset certain session states. These are done here as resetting within pages constrains script behavior (state will always be set to the default value initialized by the script)
def reset_select_session_states():
    # reset Word Details editability
    if "edit_mode" in st.session_state:
        del st.session_state.edit_mode

def indicate_notes_exist(notes):
    if (notes):
        return "✔"
    else:
        return "✕"
    
# ==========
# STATS for Dashboard
# ==========

def build_time_df():
    words = db.words_over_time()
    chars = db.characters_over_time()

    df_words = pd.DataFrame(words, columns=["date", "word_count"])
    df_chars = pd.DataFrame(chars, columns=["date", "char_count"])

    df_words["date"] = pd.to_datetime(df_words["date"])
    df_chars["date"] = pd.to_datetime(df_chars["date"])

    df = pd.merge(df_words, df_chars, on="date", how="outer").fillna(0)
    df = df.sort_values("date").set_index("date")

    # Fill missing days
    full_range = pd.date_range(df.index.min(), df.index.max())
    df = df.reindex(full_range, fill_value=0)

    # Cumulative
    df["word_cum"] = df["word_count"].cumsum()
    df["char_cum"] = df["char_count"].cumsum()

    return df

def compute_metrics(df):
    latest = df.iloc[-1]

    if len(df) > 1:
        prev = df.iloc[-2]
    else:
        prev = df.iloc[-1]

    word_total = int(latest["word_cum"])
    char_total = int(latest["char_cum"])

    word_delta = int(latest["word_cum"] - prev["word_cum"])
    char_delta = int(latest["char_cum"] - prev["char_cum"])

    return word_total, word_delta, char_total, char_delta
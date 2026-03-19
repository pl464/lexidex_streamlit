"""
Commands to run this locally (Assuming Home Directory)
C:/Users/17322/Documents/vocab_tool_test/.venv/Scripts/Activate.ps1 
cd Documents/vocab_tool_test
streamlit run Dashboard.py
"""

import streamlit as st
import pandas as pd
import db
from utils import *
# from streamlit_extras.stylable_container import stylable_container

# -------------------------
# Setup
# -------------------------

# ----- Load CSS -----
def load_css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ----- Streamlit Setup -----
reset_select_session_states()
st.set_page_config(page_title="My Lexicon", page_icon="📖", layout='wide', initial_sidebar_state='collapsed')

# session state variable for form validation
if "confirm_submit" not in st.session_state:
    st.session_state.confirm_submit = False

# session state variable for entry update toast
if "entry_added_toast" not in st.session_state:    
    st.session_state.entry_added_toast = False

# session state variable for entry update toast
if "entry_updated_toast" not in st.session_state:    
    st.session_state.entry_updated_toast = False

# session state variable for encounter add toast
if "encounter_added_toast" not in st.session_state:    
    st.session_state.encounter_added_toast = False

# handle showing toast for Entry add, update and Encounter add
if (st.session_state.entry_added_toast):
    change_green_toast_color()
    st.toast("Entry added!")
    st.session_state.entry_added_toast = False # reset
if (st.session_state.entry_updated_toast):
    change_green_toast_color()
    st.toast("Entry updated!") 
    st.session_state.entry_updated_toast = False
if (st.session_state.encounter_added_toast):
    change_green_toast_color()
    st.toast("Encounter added!") 
    st.session_state.encounter_added_toast = False

# ----- Variable declarations -----
all_tags = db.get_all_tags()

DASHBOARD_REFERENCE_WIDTH = 1000

# ----- Local debugging -----
print("*** Running code at the top of app.py. ***")
print("db.all_words() is currently:", db.all_words())
print("db.get_all_tags() is currently:", db.get_all_tags(), '\n')

# -------------------------
# Title
# -------------------------
st.title("📌 Lexidex Dashboard")
st.space()

# -------------------------
# Counts
# -------------------------

df = build_time_df()
word_total, word_delta, char_total, char_delta = compute_metrics(df)

row = st.container(horizontal=True)

with row:
    st.metric(
        "Words",
        word_total,
        delta=word_delta,
        chart_data=df["word_cum"],
        chart_type="line",
        border=True,
        delta_description="today",
        width=int(DASHBOARD_REFERENCE_WIDTH/2-10),
    )

    st.metric(
        "Characters",
        char_total,
        delta=char_delta,
        chart_data=df["char_cum"],
        chart_type="line",
        border=True,
        delta_description="today",
        width=int(DASHBOARD_REFERENCE_WIDTH/2-10),
    )
# with c3:
#     plot_df = df[["word_cum", "char_cum"]].rename(
#         columns={"word_cum": "Words", "char_cum": "Characters"}
#     )

#     st.line_chart(plot_df, height=220, )

    # start, end = st.date_input(
    #     "Date range",
    #     [df.index.min(), df.index.max()]
    # )

    # df = df.loc[start:end]

st.divider()

# -------------------------
# Dialogs
# -------------------------

@st.dialog("This entry already exists!")       
def existing_word_dialog(word_id, text, old_pron, old_meaning, new_pron, new_meaning, source, example, tags):
    if (source or example):
        st.write("The Encounter you provided will still be added if you hit \"Confirm\". Would you like to update the main meaning / pronunciation?")
    else:
        st.write("Would you like to update the main meaning / pronunciation?")

    update_main = st.radio(
        label="[PLACEHOLDER]", label_visibility='collapsed', 
        options=["No", "Yes"],
        index=0
    )

    disable_fields = (update_main == "No")

    meaning = st.text_input("Meaning", value=old_meaning or "", disabled=disable_fields)
    pron = st.text_input("Pronunciation", value=old_pron or "", disabled=disable_fields)

    c1, c2 = st.columns(2)
    
    with c1:
        if st.button("Confirm", type="primary"):
            
            if update_main == "Yes":
                db.update_word(word_id, text, pron, meaning)
                st.session_state.entry_updated_toast = True
            if (source or example):
                db.add_encounter(word_id, source, example, date)
                st.session_state.encounter_add_toast = True
    
            st.rerun()

    with c2:
        if st.button("Cancel"):
            st.rerun()
    
@st.dialog("Missing Entry")       
def empty_entry_dialog():
    st.write("You need to add an entry!")

@st.dialog("Missing information")
def empty_info_dialog():
    st.write("You're missing the meaning, pronunciation, or tags. Do you want to submit anyway?")
    if st.button("Confirm"):
        st.session_state.confirm_submit = True
        st.rerun()

# -------------------------
# Add Entry Form
# -------------------------

with st.form("word_form", clear_on_submit=True, width=DASHBOARD_REFERENCE_WIDTH):

    st.subheader("Add Entry")
    entry = st.text_input("[PLACEHOLDER]", placeholder="Enter a word, phrase, structure, etc...", label_visibility="collapsed")
    # st.divider()
    st.markdown(f"<hr style=\"font-size:0px\"></hr>", unsafe_allow_html=True)

    st.subheader("Entry Details")
    meaning = st.text_input("Meaning(s)")
                            # help='Multiple meanings suggestion: separate by semicolons')
    pronunciation = st.text_input("Pronunciation(s)")
                                  # help="Multiple pronunciations suggestion: separate by semicolons")
    tags = st.multiselect("Tags", options=all_tags, accept_new_options=True)
    notes = st.text_area("Notes", )

    st.markdown(f"<hr style=\"font-size:0px\"></hr>", unsafe_allow_html=True) # horizontal line with refined spacing

    st.subheader("Initial Encounter")
    source = st.text_input("Source", placeholder="a person, media, event, etc...")
    example = st.text_input("Example")
    encounter_notes = st.text_input("Encounter Notes")
    
    date = st.date_input("Date")

    st.space("small")
    submitted = st.form_submit_button("Add entry", type='primary')
    st.space("xxsmall")

# ----- Handle various cases upon Submit button click -----
if submitted:
    # ----- 1. entry already exists + prompt user for potential update -----
    existing = db.get_word_by_text(entry.strip())
    if existing:
        wid, _, old_meaning, old_pron, = existing
        existing_word_dialog(
            wid,
            entry,
            old_pron,
            old_meaning,
            pronunciation,
            meaning,
            source,
            example,
            tags
        )
        # ----- 2. meaning or pronunciaiton is missing + prompt user to confirm it's OK -----
    else:
        missing_fields = not meaning.strip() or not pronunciation.strip()
        entry_added = entry.strip()

        if not entry_added:
            empty_entry_dialog()
        elif missing_fields:
            empty_info_dialog()
        else:
            st.session_state.confirm_submit = True

# ----- Handle a legit submit -----
if st.session_state.confirm_submit:

    wid = db.create_word(user_id, entry.strip(), meaning.strip(), pronunciation.strip(), notes.strip())

    # handle new tag creation
    for tag in tags: 
        if tag not in all_tags:
            print("Confirmed submit. Adding tag:", tag)
            db.add_tag(tag)
    print("Confirmed submit. Updated db.get_all_tags():", db.get_all_tags())
    
    db.update_word_tags(wid, tags)

    db.add_encounter(wid, source, example, date, encounter_notes)
    db.link_word_chars(wid, entry)

    # st.success("New word added.")
    # print("NEW WORDS LIST:", db.all_words())
    st.session_state.confirm_submit = False # reset
    st.session_state.entry_added_toast = True
    st.rerun()
import streamlit as st
import db
import pandas as pd
from utils import *

# -------------------------
# Setup
# -------------------------

# -------- Data Setup --------
wid = st.session_state.get("word_id")
if not wid:
    st.warning("No word selected. Go to the Words tab and select a word!")
    st.stop()

rows = db.word_encounters(wid)

df = pd.DataFrame(
    rows,
    columns=["id", "Date", "Source", "Example", "Notes"] # Notes # TODO: notes 
)
df['Date'] = df['Date'].apply(lambda x: pretty_time(x))

word = db.word_detail(wid)
print("Word is", word)
tags = db.get_tags_for_word(wid)
all_tags = db.get_all_tags()

# ----- Session State -----

# session state variable for edits
if "entry_edited" not in st.session_state:
    st.session_state.entry_edited = False
if "meaning_edited" not in st.session_state:
    st.session_state.meaning_edited = False
if "pronunciation_edited" not in st.session_state:
    st.session_state.pronunciation_edited = False
if "tags_edited" not in st.session_state:
    st.session_state.tags_edited = False
if "notes_edited" not in st.session_state:
    st.session_state.notes_edited = False

if "encounter_added" not in st.session_state:
    st.session_state.encounter_added = False
if "encounter_edited" not in st.session_state:
    st.session_state.encounter_edited = False
if "encounter_deleted" not in st.session_state:
    st.session_state.encounter_deleted = False

# session state for edit mode (reset by reset_session_states())
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# session state for editability
def toggle_edit():
    st.session_state.edit_mode = not st.session_state.edit_mode

# show toast given state variable
if (st.session_state.entry_edited):
    change_green_toast_color()
    st.toast("Entry text updated!", duration="short")
    st.session_state.entry_edited = False # reset
# show toast given state variable
if (st.session_state.meaning_edited):
    change_green_toast_color()
    st.toast("Entry's meaning updated!", duration="short")
    st.session_state.meaning_edited = False # reset
# show toast given state variable
if (st.session_state.pronunciation_edited):
    change_green_toast_color()
    st.toast("Entry's pronunciation updated!", duration="short")
    st.session_state.pronunciation_edited = False # reset
# show toast given state variable
if (st.session_state.tags_edited):
    change_green_toast_color()
    st.toast("Entry's tags updated!", duration="short")
    st.session_state.tags_edited = False # reset
if (st.session_state.notes_edited):
    change_green_toast_color()
    st.toast("Entry's notes updated!", duration="short")
    st.session_state.notes_edited = False # reset

if (st.session_state.encounter_added):
    change_green_toast_color()
    st.toast("Encounter added!", duration="short")
    st.session_state.encounter_added = False # reset
if (st.session_state.encounter_edited):
    change_green_toast_color()
    st.toast("Encounter updated!", duration="short")
    st.session_state.encounter_edited = False # reset
if (st.session_state.encounter_deleted):
    change_red_toast_color()
    st.toast("Encounter deleted!", duration="short")
    st.session_state.encounter_deleted = False # reset

# ----- Load General CSS -----
def load_css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ----- Page-specific CSS -----
st.markdown(f"""
<style>

/* Target ONLY this button via widget key */
.st-key-edit_toggle_button {{
    background-color: {"#c9c8c0b5" if st.session_state.edit_mode else "transparent"};
    color: {"black" if st.session_state.edit_mode else "black"};
    border: 1px blue;
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s ease;
}}

/* Hover */
.st-key-edit_toggle_button:hover {{
    background-color: #c9c8c0b5;
    color: black;
    border: 1px transparent;
}}

.st-key-edit_toggle_button:active {{
    background-color: #aaa;
    color: black;
    border: 1px transparent;
    transform: scale(0.95);
}}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.st-key-word_edit_area textarea {
    font-size: 100px !important;
    line-height: 1.1;
    font-weight: 500;
    padding: 10;
    border: none;
    background: transparent;
    resize: none;
}
div[data-widget-key="word_edit"] textarea:focus {
    outline: none;
    box-shadow: none;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.st-key-notes_edit_area textarea {
    color: black;
    line-height: 1.1;
    padding: 10;
    border: none;
    background: transparent;
    resize: none;
}
div[data-widget-key="notes_edit"] textarea:focus {
    outline: none;
    box-shadow: none;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Dialogs
# -------------------------

@st.dialog("Unable to edit")       
def existing_word_dialog(old_word, existing_id):
    st.text(f"The entry \"{old_word}\" already exists.")
    pass
    # st.text(f"Would you like to go to the page for {old_word}?")
    
    # c1, c2 = st.columns(2)
    # with c1:
    #     if st.button(label="Go", type="primary"):
    #         st.session_state.word_id = int(existing_id)
    #         st.session_state.edit_mode = False # this is a session state in Word_Detail
    #         st.switch_page("pages/Word_Detail.py")
    #         reset_select_session_states()
    #         st.rerun()

    # with c2:
    #     if st.button("Cancel"):

    #         st.rerun()

@st.dialog("Confirm Deletion")       
def delete_confirm_dialog(word_id):
    st.write("This will delete the selected Entries and all their Encounters. Do you also want to delete any associated Characters? (This will also delete any Characters that no longer have any Entries associated with it.)")
    
    delete_associated_chars = st.radio(
        label="[PLACEHOLDER]",
        label_visibility='collapsed',
        options=["No", "Yes"],
        index=0
    )

    delete_chars = True if delete_associated_chars == 'Yes' else False

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Confirm", type="primary"):
            db.delete_row(word_id, delete_chars)
            st.session_state.entry_deleted_toast = True
            st.session_state.word_id = None # so that Word Detail page isn't accessing a non-existint entry
            st.switch_page("pages/1_Words.py")
    with c2:
        if st.button("Cancel"):
            st.rerun()

# -------------------------
# Entry Edit Functionality
# -------------------------
def word_update():
    _, old_word, pron, meaning = db.get_word_by_id(wid)
    new_word = st.session_state.word_edit_area

    if (new_word != old_word):
        existing = db.get_word_by_text(new_word.strip())
        if existing:
            st.session_state.word_edit_area = old_word
            existing_wid, existing_word, existing_meaning, existing_pron = existing
            existing_word_dialog(existing_word, existing_wid)
        else:
            db.update_word(wid, new_word, pron, meaning)
            db.link_word_chars(wid, new_word)
            st.session_state.entry_edited = True

def meaning_update():
    _, text, pron, old_meaning, notes = db.get_word_by_id(wid)
    new_meaning = st.session_state.meaning_text
    db.update_word(wid, text, pron, new_meaning, notes)
    st.session_state.meaning_edited = True

def pronunciation_update():
    _, text, old_pron, meaning, notes = db.get_word_by_id(wid)
    new_pron = st.session_state.pronunciation_text
    db.update_word(wid, text, new_pron, meaning, notes)
    st.session_state.pronunciation_edited = True

def notes_update():
    _, text, pron, meaning, old_notes = db.get_word_by_id(wid)
    new_notes = st.session_state.notes_edit_area
    db.update_word(wid, text, pron, meaning, new_notes)
    st.session_state.notes_edited = True

def tags_update():
    new_tags = st.session_state.edit_tags
    # handle new tag creation
    for tag in new_tags: 
        if tag not in all_tags:
            print("New tag detected. Adding tag:", tag)
            db.add_tag(tag)
    print("Confirmed tags update. Updated db.get_all_tags():", db.get_all_tags())
    
    db.update_word_tags(wid, new_tags)
    st.session_state.tags_edited = True

# -------------------------
# Display
# -------------------------

edit_mode_disabled = not st.session_state.edit_mode

# -------- Back --------


row = st.container(horizontal=True)

if (edit_mode_disabled):
    header_c1, header_c2 = st.columns(2)

    with header_c1:
        if st.button("← Back to Words"):
            st.switch_page("pages/1_Words.py")

    with header_c2:
        row = st.container(horizontal=True, horizontal_alignment='right')
        with row:
            st.button(
                "✏️ Edit Entry",
                key="edit_toggle_button",
                on_click=toggle_edit,
                type="secondary",
            )
        
        # if st.session_state.edit_mode:
        #     if st.button("🗑 Delete", type='primary'):
        #         delete_confirm_dialog(wid)
else:
    header_c1, header_c2 = st.columns(2)

    with header_c1:
        if st.button("← Back to Words"):
            st.switch_page("pages/1_Words.py")
        
    with header_c2:
        row = st.container(horizontal=True, horizontal_alignment='right')
        with row:
            st.button(
                "✔️ Done",
                key="edit_toggle_button",
                on_click=toggle_edit,
                type="secondary",
            )
            if st.button("🗑 Delete Entry", type='primary'):
                delete_confirm_dialog(wid)
    
    # with header_c3:


# -------- Entry Display --------
# st.markdown(f"<div class='big-text'>{word[1]}</div>", unsafe_allow_html=True, )

c1, c2 = st.columns([1, 1])  # Adjust width ratio as needed

# print("EDIT MODE:", st.session_state.edit_mode)
with c1:
    if st.session_state.edit_mode:
        st.text_area(
            "Word",
            value=word[1],
            label_visibility="collapsed",
            height=140,   # match markdown size
            key="word_edit_area",
            on_change=word_update,
        )
    else:
        st.markdown(
            f"<div class='big-text'>{word[1]}</div>",
            unsafe_allow_html=True,
        )

with c2:
    st.text_area(label="Notes", key='notes_edit_area', value=word[4], disabled=edit_mode_disabled, height=140, on_change=notes_update)
    # if st.session_state.edit_mode:
    #     st.text_area(
    #         "Notes",
    #         value=word[4],
    #         height=140,
    #         key="notes_edit_area"
    #     )
    # else:
    #      st.text_area(
    #         "Notes",
    #         value=word[4],
    #         disabled=True,
    #         height=140
    #     )       
    
    # mode = st.segmented_control(
    #     label="edit button",
    #     label_visibility="collapsed",
    #     options=["✏️ Edit"],
    #     key='edit_mode_toggled'
    # )

    # st.button(
    #     "✏️ Edit",
    #     key="edit_toggle_button",
    #     on_click=toggle_edit,
    #     type="secondary",
    # )
    
    # if st.session_state.edit_mode:
    #     if st.button("🗑 Delete", type='primary'):
    #         delete_confirm_dialog(wid)

# st.session_state.edit_mode = (mode == "✏️ Edit")

# ----- Tag Display -----
if not st.session_state.edit_mode:
    tag_badge_markdown = ""
    for tag in tags:
        tag_badge_markdown += f":green-badge[{tag}]"
    st.markdown(tag_badge_markdown)
else:
    edited_tags = st.multiselect(
        "Tags",
        options=all_tags,
        default=tags,
        key="edit_tags",
        on_change=tags_update
    )

# ----- Key Info (Meaning, Pronunciation) Display -----
st.text_input(label="Meaning(s)", key='meaning_text', value=word[3], disabled=edit_mode_disabled, on_change=meaning_update)
st.text_input(label="Pronunciation(s)", key='pronunciation_text', value=word[2], disabled=edit_mode_disabled, on_change=pronunciation_update)

# -------- 
# Encounters 
# --------

# ----- Encounter Edit Functionality ----
DATA_EDITOR_KEY = 'data_editor_key'

def handle_table_edit():
    if (DATA_EDITOR_KEY in st.session_state):
        rows_edited = st.session_state[DATA_EDITOR_KEY]['edited_rows']
        rows_deleted = st.session_state[DATA_EDITOR_KEY]['deleted_rows']
        if (rows_edited):
            for row_id, edit in rows_edited.items(): # this is a for loop, but rows_edited should only ever be 1 item long due to st.rerun() below
                word_id = wid
                encounter_id = int(df.loc[row_id, 'id'])
                
                # if (edit.get("delete_icon")): # handle deletes
                #     pass
                    # delete_confirm_dialog(word_id)
                # else:
                source, example, date_added, notes = db.get_encounter_by_id(encounter_id)
                
                updated_source = edit.get('Source', source)
                updated_example = edit.get('Example', example)
                updated_date = edit.get('Date Added', date_added)
                updated_notes = edit.get('Notes', notes)
                # _, old_word, old_pronunciation, old_meaning, notes_placeholder = db.get_word_by_id(word_id) # "_" is word_id, which is redundant
                # updated_word = edit.get('Word', old_word)
                
                # go through fields
                # updated_pronunciation = edit.get('Pronunciation', old_pronunciation)
                # updated_meaning = edit.get('Meaning', old_meaning)
                # db.update_word(word_id, updated_word, updated_pronunciation, updated_meaning)

                db.update_encounter(word_id, encounter_id, updated_source, updated_example, updated_date, updated_notes)
                st.session_state.encounter_edited = True
                # st.session_state.table_edited_toast = True
                st.rerun()
        elif (rows_deleted):
            for row_id in rows_deleted: # this provides a list row_ids changed which must be mapped to the encounter id in the actual database (this is located in the DF)
                word_id = wid
                encounter_id = int(df.loc[row_id, 'id'])
                db.delete_encounter(word_id, encounter_id)
                st.session_state.encounter_deleted = True
                st.rerun()

# ----- Encounter Display Table -----
st.divider()
st.subheader("Encounters", help="Edit encounters directly in this table. To add an encounter, use the section below.")
# st.caption()

# df.to_csv("TEMP.csv")
event = st.data_editor(
    df,
    key=DATA_EDITOR_KEY,
    on_change=handle_table_edit(),
    num_rows='delete',
    # selection_mode="single-cell",
    # on_select="rerun", # lambda: on_row_select(event.selection),
    column_config = {
        "id": None,
        "Date": st.column_config.TextColumn( # https://docs.streamlit.io/develop/api-reference/data/st.column_config/st.column_config.textcolumn
            "Date Added",
            help="When this encounter was added",
            width="small",
        ),
        "Source": st.column_config.TextColumn(
            "Source",
        ),
        "Example": st.column_config.TextColumn(
            "Example",
            width='large'
        ),
        "Notes": st.column_config.TextColumn(
            "Encounter Notes",
            width='large'
        ),
    },
    # hide_index=True   
)

# st.session_state[DATA_EDITOR_KEY]) # display edits for debuggery

st.divider()

# -------- Add Encounter --------
st.subheader("➕ Add Encounter")

with st.form("add_enc", clear_on_submit=True):
    source = st.text_input("Source")
    example = st.text_area("Example")
    date = st.date_input("Date")
    notes = st.text_area("Encounter Notes")
    # tags = st.text_input("Tags")
    add = st.form_submit_button("Add")

if add:
    db.add_encounter(wid, source, example, date, notes)
    st.success("Encounter added.")
    st.session_state.encounter_added = True
    st.rerun()
import streamlit as st
import pandas as pd
import db
from utils import * 

# -------------------------
# Setup
# -------------------------
reset_select_session_states()

# ----- DataFrame -----

# rows = db.all_words()
df = db.all_words()

# df = pd.DataFrame(
#     rows,
#     columns=["id", "Word", "Meaning", "Pronunciation", "Last Seen", "Notes"]
# )

st.write("Loading tags into DF")
# df['Tags'] = df['id'].apply(lambda x: db.get_tags_for_word(x)) # .apply() is not very efficient given postgres syntax which returns queries 
tags_map = db.get_word_id_to_tags_mapping()
df["Tags"] = df["id"].map(tags_map).apply(lambda x: x or [])

st.write("Running last seen")
# df['Last Enc.'] = df['last_seen'].apply(lambda x: pretty_time(x))
df['Last Seen'] = df['last_seen'].astype(str)
st.write("Running encounter count")

counts = db.encounter_counts()
df['Num Encounters'] = df['id'].map(counts).fillna(0).astype(int)

# df['Num Encounters'] = df['id'].apply(lambda x: db.encounter_count(x))


st.write("Running notes")
df['Notes?'] = df['notes'].apply(lambda x: indicate_notes_exist(x))
df = df.drop(columns=["last_seen", "notes"])

st.download_button(
    "Press to Download",
    df.to_csv().encode('utf-8'),
    "file.csv",
    "text/csv",
    key='download-csv'
)

# ----- Session State -----

# session state variable for whether the table was just edited (toast)
if "table_edited_toast" not in st.session_state:
    st.session_state.table_edited_toast = False
# session state variable for whether an entry was just deleted (toast)
if "entry_deleted_toast" not in st.session_state:
    st.session_state.entry_deleted_toast = False

# handle showing toast for Table edit
if (st.session_state.table_edited_toast):
    change_green_toast_color()
    st.toast("Table updated.", duration="short")
    st.session_state.table_edited_toast = False # reset
# handle showing toast for Entry delete
if (st.session_state.entry_deleted_toast):
    change_red_toast_color()
    st.toast("Entry deleted.", duration="short")
    st.session_state.entry_deleted_toast = False # reset

# ----- Declarations -----
DATA_EDITOR_KEY = 'data_editor_key'

# -------------------------
# Title
# -------------------------

st.title("🌳 Entries (Words)")
st.space()

# ---------------- Search ----------------
search = st.text_input("Search (Word)", width=500)

if search:
    df = df[
        # df["Word"].str.contains(search, case=False, na=False) 
        df["text"].str.contains(search, case=False, na=False) 
        # toggle the below lines to search by Meaning as well
        # | 
        # df["Meaning"].str.contains(search, case=False, na=False)
    ]

# ---------------- Tags ----------------
st.write("Loading tags")
all_tags = db.get_all_tags()

tag_filter = st.multiselect("Filter by tag", all_tags, width=500)

if tag_filter:
    keep_ids = []
    for wid in df["id"]:
        tags = db.get_tags_for_word(wid)
        if all(t in tags for t in tag_filter): # instead of all(), could also be any() for a more lenient/inclusive filter
            keep_ids.append(wid)
    df = df[df["id"].isin(keep_ids)]

# ---------------- Sorting ---------------- # seems somewhat redundant for now due to existing dataframe sorting capabilities
# sort_col = st.selectbox(
#     "Sort by",
#     ["Word", "Last Seen", "Meaning"]
# )
# df = df.sort_values(sort_col)
# direction = st.radio("Order", ["Ascending", "Descending"], horizontal=True)
# ascending = direction == "Ascending"
# df = df.sort_values(sort_col, ascending=ascending)
# df = df.reset_index(drop=True)

# -------------------------
# Dialogs
# -------------------------

# @st.dialog("Confirm Deletion")       
# def delete_confirm_dialog(word_id):
#     st.write("This will delete the selected Entries and all their Encounters. Do you also want to delete any associated Characters? (This will also delete any Characters that no longer have any Entries associated with it.)")
    
#     delete_associated_chars = st.radio(
#         label="[PLACEHOLDER]",
#         label_visibility='collapsed',
#         options=["No", "Yes"],
#         index=0
#     )

#     delete_chars = True if delete_associated_chars == 'Yes' else False

#     c1, c2 = st.columns(2)
#     with c1:
#         if st.button("Confirm", type="primary"):
#             db.delete_row(word_id, delete_chars)
#             st.session_state[DATA_EDITOR_KEY]['edited_rows'] = [] # get rid of condition that triggers delete confirm dialog
#             st.session_state.table_edited_toast = True
#             st.rerun()
#     with c2:
#         if st.button("Cancel"):
#             st.session_state[DATA_EDITOR_KEY]['edited_rows'] = [] # get rid of the condition that triggers delete confirm dialog
#             st.rerun()

# -------------------------
# Table Display/Functionality
# -------------------------

st.divider()

mode = st.segmented_control(
    "View mode",
    label_visibility="collapsed",
    options=["🔍 View", "✏️ Edit"],
    default="🔍 View",
)

if (mode == None): # prevents there from being no table from showing up (a required option for st.segmented_control is not currently supported)
    mode = "🔍 View"

column_config = {
            "id": None,
            "text": st.column_config.TextColumn( # https://docs.streamlit.io/develop/api-reference/data/st.column_config/st.column_config.textcolumn
                "Word",
                help="Click a Word for more info"
            ),
            "meaning": st.column_config.TextColumn( # https://docs.streamlit.io/develop/api-reference/data/st.column_config/st.column_config.textcolumn
                "Meaning",
                width='large',
            ),
            "tags": st.column_config.MultiselectColumn(
                "Tags",
                options=db.get_all_tags(), # implicitly required to consistently assign colors to tags
                color="auto",
                width='large',
                accept_new_options=True,
            ),
            "Last Seen": st.column_config.TextColumn(
                "Last Seen",
                # width=70,
                disabled=True,
            ),
            "Num Encounters": st.column_config.NumberColumn(
                "Enc",
                # width=30,
                disabled=True,
            ),
            "Notes?": st.column_config.TextColumn(
                "Notes",
                
            ),
        }

def handle_table_edit():
    if (DATA_EDITOR_KEY in st.session_state):
        rows_edited = st.session_state[DATA_EDITOR_KEY]['edited_rows']
        if (rows_edited):
            for row_id, edit in rows_edited.items(): # this is a for loop, but rows_edited should only ever be 1 item long due to st.rerun() below
                word_id = int(df.loc[row_id, 'id'])

                if (edit.get("delete_icon")): # handle deletes
                    pass
                    # delete_confirm_dialog(word_id)
                else:
                    _, old_word, old_pronunciation, old_meaning, notes_placeholder = db.get_word_by_id(word_id) # "_" is word_id, which is redundant
                    updated_word = edit.get('Word', old_word)
                    
                    updated_pronunciation = edit.get('Pronunciation', old_pronunciation)
                    updated_meaning = edit.get('Meaning', old_meaning)
                    db.update_word(word_id, updated_word, updated_pronunciation, updated_meaning, notes_placeholder) # note that notes is not updated here

                    updated_tags = edit.get('Tags', []) # list
                    db.update_word_tags(word_id, updated_tags)
                    
                    st.session_state.table_edited_toast = True
                    st.rerun()

if mode == "✏️ Edit":
    st.caption("Make edits to the table (Pronunciation, Meaning, or Tags)")
    # df['delete_icon'] = False #  NOTE: Likely will not be used; pending implementation of ButtonColumn
    editor_df = st.data_editor(
        df,
        column_order=("delete_icon", "Word", "Meaning", "Pronunciation", "Tags", ),
        width='content',
        height='content',
        key=DATA_EDITOR_KEY,
        # selection_mode="single-cell",
        column_config = column_config, # NOTE: if something like ButtonColumn is ever implemented by the Streamlit team, I can edit collumn_config, defined above this, to toggle a delete column (e.g. change from None to a column); alternative is just to have another config for edit mode
        on_change=handle_table_edit(),
        num_rows='fixed',
        hide_index=False,
    )
    # st.write(st.session_state[DATA_EDITOR_KEY])
elif mode == "🔍 View":
    st.caption("Click a Word to view details/encounters")
    event = st.dataframe(
        df,
        # column_order=("", "Word", "Meaning", "Pronunciation", "Tags", "Last Enc.", "Enc", "Notes"),
        key="df",
        selection_mode="single-cell",
        on_select="rerun",
        width='content',
        height='content',
        column_config = column_config,
        # hide_index=True
    )
    if (event and event['selection']['cells']): # handles clicking on the st.dataframe. See Example at https://docs.streamlit.io/develop/api-reference/data/st.dataframe
        print("Event detected:", event)
        selected_cell = event['selection']['cells'][0]
        row_id = selected_cell[0]
        col_id = selected_cell[1]
        if (col_id == 'text'):
            print("ROW NUM:", row_id)
            word_id = int(df.loc[row_id,"id"])
            print("WORD ID:", word_id)

            st.session_state.word_id = word_id
            st.session_state.word_tags = tags_map.get(word_id, []) # This was introduced 3/26 in attempt to minimize queries=

            st.session_state.edit_mode = False # this is a session state in Word_Detail
            st.switch_page("pages/3_Word_Detail.py") 
            # print("Success!")
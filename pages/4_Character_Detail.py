import streamlit as st
import db
from utils import *
import pandas as pd

reset_select_session_states()

# -------------------------
# Setup
# -------------------------

# ----- Load General CSS -----
def load_css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ----- Loading -----
cid = st.session_state.get("char_id")
if not cid:
    st.warning("No character selected.")
    st.stop()

# ----- Session State -----

# session state variable for whether notes was just edited (for toast)
if "notes_edited_toast" not in st.session_state:
    st.session_state.notes_edited_toast = False

# handle showing toast for Notes update
if (st.session_state.notes_edited_toast):
    change_green_toast_color()
    st.toast("Notes updated.", duration="short")
    st.session_state.notes_edited_toast = False # reset

# ----- Edit Functionality -----
def update_notes():
    updated_notes = st.session_state.notes_area
    db.update_char_notes(cid, updated_notes)
    st.session_state.notes_edited_toast = True

# -------------------------
# Display
# -------------------------

if st.button("← Back to Characters"):
    st.switch_page("pages/2_Characters.py")

# ----- Top Row ----    
char, notes = db.character_detail(cid)[1:]
# st.title(char)

c1, c2 = st.columns([2, 5])  # Adjust width ratio as needed

with c1:
    st.markdown(
    f"<div class='big-text'>{char}</div>",
    unsafe_allow_html=True,
)
with c2:
    st.text_area("Notes", key='notes_area', value=notes, height=200, on_change=update_notes)

# ----- Entries Display ----    
st.divider()
st.subheader("Entries with this character")
words_for_char = db.words_for_char(cid)

# create dataframe
rows = []
for word in words_for_char:
    word_id, text, meaning, pronunciation, notes = db.get_word_by_text(word)
    tags = db.get_tags_for_word(word_id)
    rows.append((word_id, text, meaning, pronunciation, tags, notes))
    
df = pd.DataFrame(
    rows,
    columns=["id", "Word", "Pronunciation", "Meaning", "Tags", "Entry Notes"]
)

# display dataframe
column_config = {
            "id": None,
            "Word": st.column_config.TextColumn( # https://docs.streamlit.io/develop/api-reference/data/st.column_config/st.column_config.textcolumn
                "Word",
                help="Click a Word for more info"
            ),
            "Meaning": st.column_config.TextColumn( # https://docs.streamlit.io/develop/api-reference/data/st.column_config/st.column_config.textcolumn
                "Meaning",
                width='large',
            ),
            "Tags": st.column_config.MultiselectColumn(
                "Tags",
                options=db.get_all_tags(), # implicitly required to consistently assign colors to tags
                color="auto",
                width='large',
                accept_new_options=True,
            ),
        }

st.caption("Click a Word to view details/encounters")
event = st.dataframe(
    df,
    key="df",
    selection_mode="single-cell",
    on_select="rerun",
    width='content',
    height='content',
    column_config = column_config,
    # hide_index=True
)

# andle redirection
if (event and event['selection']['cells']): # handles clicking on the st.dataframe. See Example at https://docs.streamlit.io/develop/api-reference/data/st.dataframe
    print("Event detected:", event)
    selected_cell = event['selection']['cells'][0]
    row_id = selected_cell[0]
    col_id = selected_cell[1]
    if (col_id == 'Word'):
        print("ROW NUM:", row_id)
        word_id = df.loc[row_id, "id"]
        print("WORD ID:", word_id)
        st.session_state.word_id = int(word_id)
        st.session_state.edit_mode = False # this is a session state in Word_Detail
        st.switch_page("pages/3_Word_Detail.py") 
#        print("Success!")

# st.write(", ".join(db.words_for_char(cid)))

# st.divider()
# st.subheader("Notes")
# new_notes = st.text_area("", label_visibility='collapsed', value=notes, height=300)

# if st.button("Save Notes"):
#     db.update_char_notes(cid, new_notes)
#     st.success("Saved.")
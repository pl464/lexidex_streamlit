import streamlit as st
import db
from utils import *

reset_select_session_states()

st.title("🍃 Characters")
st.space()

search = st.text_input("Search character")

sort = st.selectbox("Sort by", ["Character", "Word Count"])

chars = db.all_characters()

# if sort == "Word Count":
#     chars = sorted(chars, key=lambda x: x[3], reverse=True)
# else:
#     chars = sorted(chars, key=lambda x: x[1])
if sort == "Word Count":
    chars = chars.sort_values(by="count", ascending=False)
else:
    chars = chars.sort_values(by="char")

st.divider()

# ---------------- Table ----------------
with st.container():
    st.markdown("<div class='lex-header'>", unsafe_allow_html=True)

    h1, h2, h3, h4, h5 = st.columns([1,3,1,1,3])
    h1.markdown("**Character**")
    h2.markdown("**Words**")
    h3.markdown("**# Words**")
    h4.markdown("**Notes?**")
    h5.markdown("**Notes Preview**")

    st.markdown("</div> <hr style='margin-top:2px;margin-bottom:6px'>", unsafe_allow_html=True)

# st.divider()

# for cid, char, notes, count in chars:
for cid, char, notes, count in chars.itertuples(index=False):

    if search and search not in char:
        continue

    words = db.words_for_char(cid)
    preview = ", ".join(words[:6])
    
    warn = "⚠️" if not notes.strip() else ""
    note_preview = notes[:40] + "..." if notes else ""

    c1, c2, c3, c4, c5 = st.columns([1,3,1,1,3])

    with c1:
        if st.button(char, key=cid):
            st.session_state.char_id = cid
            st.switch_page("pages/4_Character_Detail.py")

    with c2:
        st.write(preview)

    with c3:
        st.write(f"{count} words")

    with c4:
        st.write(warn)

    with c5:
        st.write(note_preview)
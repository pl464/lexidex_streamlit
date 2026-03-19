import streamlit as st
import sqlite3

conn = sqlite3.connect("words.db", check_same_thread=False)
cursor = conn.cursor()

# ── Data access ───────────────────────────────────────────────────────────────

def get_all_tags():
    """Returns list of (id, name, word_count) for every tag."""
    cursor.execute("""
        SELECT t.id, t.name, COUNT(wt.word_id) as word_count
        FROM tags t
        LEFT JOIN words_tags wt ON t.id = wt.tag_id
        GROUP BY t.id, t.name
        ORDER BY t.name COLLATE NOCASE
    """)
    return cursor.fetchall()

def rename_tag(tag_id: int, new_name: str):
    cursor.execute("UPDATE tags SET name = ? WHERE id = ?", (new_name.strip(), tag_id))
    conn.commit()

def delete_tag(tag_id: int):
    cursor.execute("DELETE FROM words_tags WHERE tag_id = ?", (tag_id,))
    cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
    conn.commit()

def merge_tags(source_id: int, target_id: int):
    """Re-point all words from source tag to target tag, then delete source."""
    cursor.execute("""
        INSERT OR IGNORE INTO words_tags (word_id, tag_id)
        SELECT word_id, ? FROM words_tags WHERE tag_id = ?
    """, (target_id, source_id))
    delete_tag(source_id)

# ── Page ──────────────────────────────────────────────────────────────────────

def render_tags_page():
    st.title("🏷️ Manage Tags")

    tags = get_all_tags()   # [(id, name, word_count), ...]

    if not tags:
        st.info("No tags yet — they'll appear here once users start tagging words.")
        return

    # ── Toolbar ───────────────────────────────────────────────────────────────
    col_search, col_sort = st.columns([3, 1])
    with col_search:
        query = st.text_input("Search tags", placeholder="Filter by name…", label_visibility="collapsed")
    with col_sort:
        sort_by = st.selectbox("Sort by", ["Name", "Word count"], label_visibility="collapsed")

    filtered = [t for t in tags if query.lower() in t[1].lower()]
    if sort_by == "Word count":
        filtered = sorted(filtered, key=lambda t: t[2], reverse=True)

    st.caption(f"{len(filtered)} of {len(tags)} tags")
    st.divider()

    # ── Tag rows ──────────────────────────────────────────────────────────────
    for tag_id, name, word_count in filtered:
        col_name, col_count, col_edit, col_delete = st.columns([4, 1, 1, 1])

        with col_name:
            st.markdown(f"**{name}**")
        with col_count:
            st.caption(f"{word_count} word{'s' if word_count != 1 else ''}")
        with col_edit:
            if st.button("Edit", key=f"edit_{tag_id}", use_container_width=True):
                st.session_state[f"editing_{tag_id}"] = True
        with col_delete:
            if st.button("Delete", key=f"del_{tag_id}", use_container_width=True, type="primary"):
                st.session_state[f"confirming_delete_{tag_id}"] = True

        # Inline edit form
        if st.session_state.get(f"editing_{tag_id}"):
            with st.container(border=True):
                other_tags = [(t[0], t[1]) for t in tags if t[0] != tag_id]

                tab_rename, tab_merge = st.tabs(["Rename", "Merge into another tag"])

                with tab_rename:
                    new_name = st.text_input("New name", value=name, key=f"rename_input_{tag_id}")
                    r1, r2 = st.columns(2)
                    with r1:
                        if st.button("Save", key=f"save_{tag_id}", use_container_width=True):
                            if new_name.strip() and new_name.strip() != name:
                                try:
                                    rename_tag(tag_id, new_name)
                                    st.success(f"Renamed to **{new_name.strip()}**")
                                    del st.session_state[f"editing_{tag_id}"]
                                    st.rerun()
                                except Exception:
                                    st.error("That name is already taken.")
                            else:
                                del st.session_state[f"editing_{tag_id}"]
                                st.rerun()
                    with r2:
                        if st.button("Cancel", key=f"cancel_edit_{tag_id}", use_container_width=True):
                            del st.session_state[f"editing_{tag_id}"]
                            st.rerun()

                with tab_merge:
                    if not other_tags:
                        st.caption("No other tags to merge into.")
                    else:
                        target = st.selectbox(
                            "Merge into",
                            options=[t[0] for t in other_tags],
                            format_func=lambda tid: next(t[1] for t in other_tags if t[0] == tid),
                            key=f"merge_target_{tag_id}",
                        )
                        st.caption("All words tagged **" + name + "** will be moved to the selected tag, then **" + name + "** will be deleted.")
                        m1, m2 = st.columns(2)
                        with m1:
                            if st.button("Merge", key=f"merge_{tag_id}", use_container_width=True, type="primary"):
                                merge_tags(tag_id, target)
                                del st.session_state[f"editing_{tag_id}"]
                                st.rerun()
                        with m2:
                            if st.button("Cancel", key=f"cancel_merge_{tag_id}", use_container_width=True):
                                del st.session_state[f"editing_{tag_id}"]
                                st.rerun()

        # Delete confirmation
        if st.session_state.get(f"confirming_delete_{tag_id}"):
            with st.container(border=True):
                st.warning(
                    f"Delete **{name}**? It's used on {word_count} word{'s' if word_count != 1 else ''}. "
                    f"The words themselves won't be deleted."
                )
                d1, d2 = st.columns(2)
                with d1:
                    if st.button("Yes, delete", key=f"confirm_del_{tag_id}", use_container_width=True, type="primary"):
                        delete_tag(tag_id)
                        del st.session_state[f"confirming_delete_{tag_id}"]
                        st.rerun()
                with d2:
                    if st.button("Cancel", key=f"cancel_del_{tag_id}", use_container_width=True):
                        del st.session_state[f"confirming_delete_{tag_id}"]
                        st.rerun()

    # ── Bulk delete unused ────────────────────────────────────────────────────
    unused = [t for t in tags if t[2] == 0]
    if unused:
        st.divider()
        if st.button(f"🗑 Delete all {len(unused)} unused tag{'s' if len(unused) != 1 else ''}", type="primary"):
            for tag_id, _, _ in unused:
                delete_tag(tag_id)
            st.rerun()


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    st.set_page_config(page_title="Tags", page_icon="🏷️", layout="centered")
    render_tags_page()
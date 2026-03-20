import sqlite3
from datetime import datetime
import streamlit as st
from sqlalchemy import text

# conn = sqlite3.connect("words.db", check_same_thread=False)
# cursor = conn.cursor()

conn = st.connection("postgresql", type="sql")
# df = conn.query('SELECT * FROM ')

# -------------------------
# Table Creation
# -------------------------

# cursor.execute("""
# CREATE TABLE IF NOT EXISTS words (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     text TEXT UNIQUE NOT NULL,
#     meaning TEXT,
#     pronunciation TEXT,
#     date_first_seen TEXT,
#     notes TEXT
# )
# """)

# cursor.execute("""
# CREATE TABLE IF NOT EXISTS encounters (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     word_id INTEGER,
#     source TEXT,
#     example TEXT,
#     date_added TEXT,
#     notes TEXT
# )
# """)

# cursor.execute("""
# CREATE TABLE IF NOT EXISTS characters (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     char TEXT UNIQUE,
#     date_added TEXT,
#     notes TEXT
# )
# """)

# cursor.execute("""
# CREATE TABLE IF NOT EXISTS word_characters (
#     word_id INTEGER,
#     char_id INTEGER,
#     PRIMARY KEY (word_id, char_id)
# )
# """)

# cursor.execute("""
# CREATE TABLE IF NOT EXISTS tags (
#     id INTEGER PRIMARY KEY,
#     name TEXT UNIQUE NOT NULL
# );
# """)

# cursor.execute("""
# CREATE TABLE IF NOT EXISTS word_tags (
#     word_id INTEGER,
#     tag_id INTEGER,
#     PRIMARY KEY (word_id, tag_id),
#     FOREIGN KEY (word_id) REFERENCES words(id),
#     FOREIGN KEY (tag_id) REFERENCES tags(id)
# );
# """)

# conn.commit()

# -------------------------
# Core Update/Query Functions
# -------------------------

# ----- Word/Entries -----

def get_word_by_text(text_val):
    df = conn.query("SELECT id, text, meaning, pronunciation, notes FROM words WHERE text = :text", params={"text": text_val})
    return df.iloc[0] if not df.empty else None
    # return cursor.fetchone()

def get_word_by_id(word_id):
    df = conn.query(
        "SELECT id, text, meaning, pronunciation, notes FROM words WHERE id = :id",
        params={"id": word_id},
        ttl=0  # disable caching so you always get fresh results
    )
    return df.iloc[0] if not df.empty else None

def create_word(text_val, meaning, pron, notes):
    with conn.session as session:
        session.execute(
            text("""
                INSERT INTO words (text, meaning, pronunciation, date_first_seen, notes)
                VALUES (:text, :meaning, :pron, :date_first_seen, :notes)
            """),
            {
                "text": text_val,
                "meaning": meaning,
                "pron": pron,
                "date_first_seen": datetime.now().isoformat(),
                "notes": notes
            }
        )
        session.commit()
    # try:
    # cursor.execute("""
    #     INSERT INTO words VALUES (NULL, ?, ?, ?, ?, ?)
    # """, (text, meaning, pron, datetime.now().isoformat(), notes))
    # conn.commit()
    # except Exception as e:
    #     print('Exception in db.py:', e)
    # return cursor.lastrowid

def update_word(word_id, text_val, pron, meaning, notes):
    with conn.session as session:
        session.execute(
            text("""
            UPDATE words SET text=:text, pronunciation=:pron, meaning=:meaning, notes=:notes WHERE id=:id
                 """),
            {"text": text_val, "pron": pron, "meaning": meaning, "notes": notes, "id": word_id}
        )
        session.commit()

# ----- Encounters -----

def get_encounter_by_id(encounter_id):
    df = conn.query(
        "SELECT source, example, date_added, notes FROM encounters WHERE id = :id",
        params={"id": encounter_id},
        ttl=0
    )
    return df.iloc[0] if not df.empty else None


def add_encounter(word_id, source, example, date, notes):
    with conn.session as session:
        session.execute(
            text("""
                 INSERT INTO encounters (word_id, source, example, date_added, notes) VALUES (:word_id, :source, :example, :date, :notes)
            """),
            {"word_id": word_id, "source": source, "example": example, "date": date, "notes": notes}
        )
        session.commit()

def encounter_count(word_id):
    df = conn.query(
        "SELECT COUNT(*) AS count FROM encounters WHERE word_id = :word_id",
        params={"word_id": word_id},
        ttl=0
    )
    return df.iloc[0]["count"]


def update_encounter(word_id, encounter_id, source, example, date_added, encounter_notes):
    with conn.session as session:
        session.execute(
            text("""
                 UPDATE encounters SET source=:source, example=:example, date_added=:date_added, notes=:notes WHERE word_id=:word_id AND id=:id
                 """),
            {"source": source, "example": example, "date_added": date_added, "notes": encounter_notes, "word_id": word_id, "id": encounter_id}
        )
        session.commit()


def delete_encounter(word_id, encounter_id):
    with conn.session as session:
        session.execute(
            text("""
                DELETE FROM encounters 
                WHERE word_id=:word_id AND id=:id
                 """),
            {"word_id": word_id, "id": encounter_id}
        )
        session.commit()

# ----- Tags -----
'''
PARAMS:
- name (str): name of tag.
RETURNS:
- nothing. adds a new tag.
'''
def add_tag(name):
    with conn.session as session:
        result = session.execute(
            text("""
                 INSERT INTO tags (name) 
                 VALUES (:name)
            """),
            {"name": name}
        )
        session.commit()
        return result.lastrowid
        
'''
PARAMS:
- word_id: `id` of word in the words table
- tags: list of tags from the app.py form
RETURNS:
- nothing. updates the word_tags Table (implements one-to-many relationship between word and its tags)
'''
def update_word_tags(word_id, new_tags):
    with conn.session as session:
        # Delete all existing relationships
        session.execute(
            text("""
                DELETE FROM word_tags 
                WHERE word_id=:word_id
                 """),
            {"word_id": word_id}
        )

        all_tags = get_all_tags()

        for tag in new_tags:
            if tag not in all_tags:
                print("This tag gon be added:", tag)
                add_tag(tag)

            # Get the tag's id
            tag_row = conn.query(
                "SELECT id FROM tags WHERE name=:name",
                params={"name": tag},
                ttl=0
            )
            tag_id = tag_row.iloc[0]["id"]

            session.execute(
                text("""
                    INSERT INTO word_tags (word_id, tag_id) 
                    VALUES (:word_id, :tag_id)
                    """),
                {"word_id": word_id, "tag_id": tag_id}
            )

        session.commit()

'''
PARAMS:
- word_id: `id` of word in the words table
RETURNS:
- list[str] of tag names for the word
'''
def get_tags_for_word(word_id):
    tag_ids_df = conn.query(
        "SELECT tag_id FROM word_tags WHERE word_id=:word_id",
        params={"word_id": word_id},
        ttl=0
    )
    tag_names = []
    for tag_id in tag_ids_df["tag_id"]:
        tag_df = conn.query(
            "SELECT name FROM tags WHERE id=:id",
            params={"id": tag_id},
            ttl=0
        )
        tag_names.append(tag_df.iloc[0]["name"])
    return tag_names

# ----- Database Edits -----
'''
PARAMS:
- word_id: `id` of word in the words table
- delete_associated_chars: Boolean for whether to delete associated characters
RETURNS:
- nothing. This handles row deletions: from the words and encounters database (assumed), characters database (if user says so). It won't delete tags that are unique to this Word.
'''

def delete_row(word_id, delete_associated_chars):
    with conn.session as session:
        session.execute(text("DELETE FROM words WHERE id=:id"), {"id": word_id})
        session.execute(text("DELETE FROM encounters WHERE id=:id"), {"id": word_id})
        session.execute(text("DELETE FROM word_tags WHERE word_id=:word_id"), {"word_id": word_id})

        if delete_associated_chars:
            session.execute(
                text("DELETE FROM word_characters WHERE word_id=:word_id"),
                {"word_id": word_id}
            )
            session.execute(text("""
                DELETE FROM characters
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM word_characters
                    WHERE word_characters.char_id = characters.id
                )
            """))

        session.commit()


# ----- Characters -----
def get_or_create_char(c):
    df = conn.query(
        "SELECT id FROM characters WHERE char=:c",
        params={"c": c},
        ttl=0
    )
    if not df.empty:
        return df.iloc[0]["id"]
    else:
        with conn.session as session:
            result = session.execute(
                text("""
                     INSERT INTO characters (char, date_added, notes) 
                     VALUES (:c, :date_added, '')
                     """),
                {"c": c, "date_added": datetime.now().isoformat()}
            )
            session.commit()
            return result.lastrowid


def link_word_chars(word_id, text_val):
    for c in text_val:
        cid = get_or_create_char(c)
        with conn.session as session:
            session.execute(
                text("""
                     INSERT INTO word_characters (word_id, char_id) 
                     VALUES (:word_id, :cid) ON CONFLICT DO NOTHING
                     """),
                {"word_id": word_id, "cid": cid}
            )
            session.commit()

# ----- Word/Entry Queries -----

def all_words():
    df = conn.query("""
        SELECT w.id, w.text, w.pronunciation, w.meaning,
               MAX(e.date_added) as last_seen, w.notes
        FROM words w
        LEFT JOIN encounters e ON w.id = e.word_id
        GROUP BY w.id
        ORDER BY last_seen DESC
    """, ttl=0)
    return df


def word_detail(word_id):
    df = conn.query(
        "SELECT id, text, pronunciation, meaning, notes FROM words WHERE id=:id",
        params={"id": word_id},
        ttl=0
    )
    return df.iloc[0] if not df.empty else None


def word_encounters(word_id):
    df = conn.query(
        "SELECT id, date_added, source, example, notes FROM encounters WHERE word_id=:word_id ORDER BY date_added DESC",
        params={"word_id": word_id},
        ttl=0
    )
    return df

# ----- Character Queries -----

def all_characters():
    df = conn.query("""
        SELECT c.id, c.char, c.notes,
               COUNT(wc.word_id) as count
        FROM characters c
        LEFT JOIN word_characters wc ON c.id = wc.char_id
        GROUP BY c.id, c.char, c.notes
        ORDER BY c.char
    """, ttl=0)
    return df

def character_detail(cid):
    df = conn.query(
        "SELECT id, char, notes FROM characters WHERE id=:id",
        params={"id": cid},
        ttl=0
    )
    return df.iloc[0] if not df.empty else None


def update_char_notes(cid, notes):
    with conn.session as session:
        session.execute(
            text("""
            UPDATE characters SET notes=:notes WHERE id=:id
                 """),
            {"notes": notes, "id": cid}
        )
        session.commit()


def words_for_char(cid):
    df = conn.query("""
        SELECT w.text FROM words w
        JOIN word_characters wc ON w.id = wc.word_id
        WHERE wc.char_id=:cid
    """, params={"cid": cid}, ttl=0)
    return df["text"].tolist()

# ----- Tags Functionalities -----

def get_all_tags():
    df = conn.query(
        "SELECT id, name FROM tags ORDER BY name",
        ttl=0
    )
    return df["name"].tolist()

# conn = sqlite3.connect("words.db", check_same_thread=False)
# cursor = conn.cursor()

def get_all_tags_dataframe():
    """Returns DataFrame of (id, name, word_count) for every tag."""
    df = conn.query("""
        SELECT t.id, t.name, COUNT(wt.word_id) AS word_count
        FROM tags t
        LEFT JOIN word_tags wt ON t.id = wt.tag_id
        GROUP BY t.id, t.name
        ORDER BY t.name
    """, ttl=0)
    return df


def rename_tag(tag_id: int, new_name: str):
    with conn.session as session:
        session.execute(
            text("""
                UPDATE tags SET name = :name WHERE id = :id
                 """),
            {"name": new_name.strip(), "id": tag_id}
        )
        session.commit()


def delete_tag(tag_id: int):
    with conn.session as session:
        session.execute(
            text("DELETE FROM word_tags WHERE tag_id = :tag_id"),
            {"tag_id": tag_id}
        )
        session.execute(
            text("DELETE FROM tags WHERE id = :id"),
            {"id": tag_id}
        )
        session.commit()


def merge_tags(source_id: int, target_id: int):
    """Re-point all words from source tag to target tag, then delete source."""
    with conn.session as session:
        session.execute(
            text("""
                INSERT INTO word_tags (word_id, tag_id)
                SELECT word_id, :target_id FROM word_tags WHERE tag_id = :source_id
                ON CONFLICT DO NOTHING
                """), 
            {"target_id": target_id, "source_id": source_id})
        session.commit()
    delete_tag(source_id)

# -------------------------
# Stats
# -------------------------

def word_count():
    df = conn.query("SELECT COUNT(*) AS count FROM words", ttl=0)
    return df.iloc[0]["count"]


def character_count():
    df = conn.query("SELECT COUNT(*) AS count FROM characters", ttl=0)
    return df.iloc[0]["count"]

def words_over_time():
    df = conn.query("""
        SELECT TO_CHAR(date_first_seen, 'YYYY-MM-DD') AS day, COUNT(*) AS count
        FROM words
        GROUP BY day
        ORDER BY day
    """, ttl=0)
    return df


def characters_over_time():
    df = conn.query("""
        SELECT TO_CHAR(date_added, 'YYYY-MM-DD') AS day, COUNT(*) AS count
        FROM characters
        GROUP BY day
        ORDER BY day
    """, ttl=0)
    return df
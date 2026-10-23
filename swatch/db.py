# -*- coding: utf-8 -*-
"""SQLite store. One row per article; articles about the same seizure share an event_id."""
import os
import re
import sqlite3
from .lexicon import norm, slug, LANG_COUNTRY

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT UNIQUE, title TEXT, title_key TEXT, source TEXT, published TEXT, fetched TEXT,
  lang TEXT, source_country TEXT, text_mode TEXT, is_demo INTEGER DEFAULT 0,
  relevant INTEGER DEFAULT 0,
  category TEXT, item TEXT, cargo TEXT, regimes TEXT, authorities TEXT, agency TEXT,
  qty_kg REAL, qty_barrels REAL, qty_units REAL, unit_type TEXT, value_usd REAL,
  vessel TEXT, imo TEXT, flag TEXT, container_numbers TEXT, transport TEXT, in_container INTEGER,
  origin TEXT, origin_place TEXT, destination TEXT, destination_place TEXT, transit TEXT,
  seizure_country TEXT, seizure_place TEXT, location_conf TEXT,
  arrests INTEGER, indicators TEXT, sanctioned_party INTEGER,
  route TEXT, corridor TEXT, mo_summary TEXT, completeness INTEGER, event_id INTEGER,
  title_en TEXT, ner_places TEXT, actor TEXT
);
CREATE INDEX IF NOT EXISTS ix_pub ON articles(published);
CREATE INDEX IF NOT EXISTS ix_event ON articles(event_id);
CREATE TABLE IF NOT EXISTS alerts(
  run_date TEXT, severity TEXT, type TEXT, title TEXT, detail TEXT, urls TEXT
);
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
"""
COLS = None


def connect(path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    global COLS
    COLS = {r["name"] for r in conn.execute("PRAGMA table_info(articles)")}
    conn.commit()
    return conn


def title_key(title, source=None):
    t = norm(title)
    if source:
        t = re.sub(r"\s+-\s+" + re.escape(norm(source)) + r"\s*$", "", t)
    t = re.sub(r"\s+-\s+[^-]{2,40}$", "", t)          # strip trailing " - Outlet"
    return slug(t)[:90]


def known_urls(conn):
    return {r[0] for r in conn.execute("SELECT url FROM articles")}


def known_title_keys(conn, days=14):
    return {r[0] for r in conn.execute(
        "SELECT title_key FROM articles WHERE date(published) >= date('now', ?)", (f"-{days} day",))}


def insert_article(conn, rec):
    keys = [k for k in rec if k in COLS]
    cur = conn.execute(f"INSERT OR IGNORE INTO articles ({','.join(keys)}) VALUES ({','.join('?' * len(keys))})",
                       [rec[k] for k in keys])
    return cur.lastrowid if cur.rowcount else None


def fix_official_site_langs(conn, site_langs):
    """Reset the language of articles found through an official-site search to the site's real language,
    so their headline is translated properly."""
    n = 0
    for site, lang in (site_langs or {}).items():
        if lang == "en":
            continue
        cur = conn.execute("UPDATE articles SET lang=?, title_en=NULL WHERE url LIKE ? AND lang='en' AND (title_en IS NULL OR title_en=title)",
                           (lang, f"%{site}%"))
        n += cur.rowcount
    if n:
        conn.commit()
    return n


def backfill_title_en(conn, translate_fn, limit=150):
    """Translate headlines stored before English titles existed or whose translation failed (oldest first)."""
    rows = conn.execute(
        "SELECT id, title, lang FROM articles WHERE relevant=1 AND lang IS NOT NULL "
        "AND lang != 'en' AND (title_en IS NULL OR title_en = '' OR title_en = title) ORDER BY id LIMIT ?", (limit,)).fetchall()
    n = 0
    for r in rows:
        en = translate_fn(r["title"], r["lang"])
        conn.execute("UPDATE articles SET title_en=? WHERE id=?", (en, r["id"]))
        n += 1
    if n:
        conn.commit()
    return n


LOCATION_COLS = ["seizure_country", "seizure_place", "location_conf", "origin", "origin_place", "destination",
                 "destination_place", "transit", "route", "corridor"]


def backfill_locations(conn, locate_fn, days=7):
    """Re-read the headline of every report that has no country yet. Only fills what is empty."""
    rows = conn.execute("SELECT id, title, COALESCE(source_country, ''), lang FROM articles WHERE relevant=1 AND seizure_country IS NULL "
                        "AND COALESCE(published, fetched) >= date('now', ?)", (f"-{int(days)} day",)).fetchall()
    gained = 0
    for r in rows:
        try:
            rec = locate_fn(r[1], r[2] or LANG_COUNTRY.get(r[3]))
        except Exception:
            continue
        if not rec.get("seizure_country"):
            continue
        sets = {c: rec.get(c) for c in LOCATION_COLS if rec.get(c) is not None}
        conn.execute("UPDATE articles SET " + ", ".join(f"{c}=?" for c in sets) + " WHERE id=?", [*sets.values(), r[0]])
        gained += 1
    conn.commit()
    return gained


_STOP = set("with from that this into after over their they were have been will which said says about more than also during near amid under "
            "police customs officers officials seized seizure seizes sanctions sanctioned sanction worth million found tanker vessel ship".split())


def _tokens(title):
    t = slug(title)
    words = {w for w in t.split() if (len(w) >= 4 or (len(w) >= 3 and not w.isascii())) and w not in _STOP}
    for run in re.findall(r"[一-鿿]+", t):
        words |= {run[i:i + 2] for i in range(len(run) - 1)}
    return words


def _jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def _days_apart(d1, d2):
    import datetime as dt
    try:
        return abs((dt.date.fromisoformat(d1[:10]) - dt.date.fromisoformat(d2[:10])).days)
    except Exception:
        return 99


def _same_amount(a, b):
    """True/False when both quantities are known and comparable; None when we cannot tell."""
    for k in ("qty_barrels", "value_usd", "qty_kg", "qty_units"):
        x, y = a[k], b[k]
        if x and y:
            return abs(x - y) / max(x, y) <= 0.08
    return None


def assign_event(conn, art_id):
    """Give a new relevant article an event_id: join an existing event when it is the same seizure.
    The same IMO number or vessel name is the strongest sign; otherwise the quantity must agree (within 8%) and the
    country or headline must match."""
    a = conn.execute("SELECT * FROM articles WHERE id=?", (art_id,)).fetchone()
    cands = conn.execute(
        "SELECT * FROM articles WHERE relevant=1 AND event_id IS NOT NULL AND id<>? "
        "AND date(published) BETWEEN date(?, '-10 day') AND date(?, '+10 day')", (art_id, a["published"], a["published"])).fetchall()
    ta = _tokens(a["title"])
    for c in cands:
        if a["imo"] and c["imo"] and a["imo"] == c["imo"] and _days_apart(a["published"], c["published"]) <= 10:
            conn.execute("UPDATE articles SET event_id=? WHERE id=?", (c["event_id"], art_id))
            return c["event_id"]
        if a["category"] != c["category"]:
            continue
        sim = _jaccard(ta, _tokens(c["title"]))
        same_ctry = bool(a["seizure_country"] and c["seizure_country"] and a["seizure_country"] == c["seizure_country"])
        same_vessel = bool(a["vessel"] and c["vessel"] and norm(a["vessel"]) == norm(c["vessel"]))
        amount = _same_amount(a, c)
        if amount is False:
            continue
        both_ctry = bool(a["seizure_country"] and c["seizure_country"])
        if same_vessel:
            match = True
        elif amount is True:
            match = same_ctry or (sim >= 0.8 if both_ctry else sim >= 0.3)
        else:
            match = sim >= 0.6 and same_ctry and _days_apart(a["published"], c["published"]) <= 3
        if match:
            conn.execute("UPDATE articles SET event_id=? WHERE id=?", (c["event_id"], art_id))
            return c["event_id"]
    conn.execute("UPDATE articles SET event_id=? WHERE id=?", (art_id, art_id))
    return art_id


def save_alerts(conn, run_date, alerts):
    conn.execute("DELETE FROM alerts WHERE run_date=?", (run_date,))
    conn.executemany("INSERT INTO alerts VALUES (?,?,?,?,?,?)",
                     [(run_date, a["severity"], a["type"], a["title"], a["detail"], "\n".join(a.get("urls", [])))
                      for a in alerts])
    conn.commit()


def get_meta(conn, key, default=None):
    row = conn.execute("SELECT v FROM meta WHERE k=?", (key,)).fetchone()
    return row["v"] if row is not None else default


def set_meta(conn, key, value):
    conn.execute("INSERT OR REPLACE INTO meta(k, v) VALUES(?, ?)", (key, str(value)))
    conn.commit()

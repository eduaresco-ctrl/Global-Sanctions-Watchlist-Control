# -*- coding: utf-8 -*-
"""
Official sanctions lists, used to name the sanctioned people, companies and vessels in a report.

Each run downloads the public lists (US OFAC SDN, UN Security Council consolidated list, EU consolidated list),
builds a name index and looks for those names in the headlines of each event. Nothing is guessed: a name is only
shown if it is written on an official list AND appears in the headlines. A list that cannot be downloaded is
skipped with a message; the run never fails because of it.

Single-word names are never matched on their own (too many false hits). Vessels are matched by IMO number
when the report has one, otherwise by a multi-word name.
"""
import csv
import io
import re
import unicodedata
import xml.etree.ElementTree as ET

import requests

UA = {"User-Agent": "Mozilla/5.0 (compatible; SanctionsSeizureWatch/1.0)"}
SOURCES = {
    "OFAC": {"sdn": ["https://www.treasury.gov/ofac/downloads/sdn.csv", "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV"],
             "alt": ["https://www.treasury.gov/ofac/downloads/alt.csv", "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ALT.CSV"]},
    "UN": {"xml": ["https://scsanctions.un.org/resources/xml/en/consolidated.xml"]},
    "EU": {"csv": ["https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw"]},
}
MAXGRAM = 8
IMO_RX = re.compile(r"\bIMO\s*(?:No\.?|number|#)?\s*:?\s*(\d{7})\b", re.I)


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _get(urls, log=print):
    for u in urls:
        try:
            r = requests.get(u, headers=UA, timeout=90)
            if r.status_code == 200 and len(r.content) > 1000:
                return r.content
            log(f"      list download {u[:70]}: HTTP {r.status_code}")
        except Exception as exc:
            log(f"      list download {u[:70]} failed: {type(exc).__name__}")
    return None


def _kind(raw):
    raw = (raw or "").strip().lower()
    if raw in ("individual", "person", "p"):
        return "Individual"
    if raw in ("vessel", "ship"):
        return "Vessel"
    if raw in ("aircraft",):
        return "Aircraft"
    return "Company"


class Index:
    def __init__(self):
        self.names = {}   # tuple(tokens) -> list of records
        self.imo = {}     # imo -> record
        self.count = {}

    def add(self, name, kind, src, prog="", imo=None):
        if "," in name and kind == "Individual":          # OFAC writes "SURNAME, Given names"
            last, _, first = name.partition(",")
            self.add(first.strip() + " " + last.strip(), kind, src, prog)
            name = first.strip() + " " + last.strip()
        tok = tuple(norm(name).split())
        rec = {"n": name.strip(), "t": kind, "l": src, "p": (prog or "").strip()}
        self.count[src] = self.count.get(src, 0) + 1
        if imo:
            self.imo[imo] = rec
        ok = len(tok) >= 2 and len(" ".join(tok)) >= (10 if kind == "Individual" else 8)
        if ok or (kind == "Vessel" and len(tok) >= 2):
            lst = self.names.setdefault(tok, [])
            if not any(r["l"] == src and r["n"] == rec["n"] for r in lst):
                lst.append(rec)


def parse_ofac(sdn_bytes, alt_bytes, idx):
    rows = list(csv.reader(io.StringIO(sdn_bytes.decode("utf-8", "replace"))))
    ent = {}
    for r in rows:
        if len(r) < 12 or not r[0].strip().isdigit():
            continue
        kind = _kind(r[2] if r[2].strip() != "-0-" else "")
        imo = None
        m = IMO_RX.search(r[11])
        if m:
            imo = m.group(1)
        ent[r[0]] = (kind, r[3])
        idx.add(r[1], kind, "OFAC", r[3], imo)
    if alt_bytes:
        for r in csv.reader(io.StringIO(alt_bytes.decode("utf-8", "replace"))):
            if len(r) >= 4 and r[0] in ent and r[3].strip() not in ("", "-0-"):
                idx.add(r[3], ent[r[0]][0], "OFAC", ent[r[0]][1])


def parse_un(xml_bytes, idx):
    root = ET.fromstring(xml_bytes)
    for kind, tag in (("Individual", "INDIVIDUAL"), ("Company", "ENTITY")):
        for el in root.iter(tag):
            prog = (el.findtext("UN_LIST_TYPE") or "").strip()
            if tag == "INDIVIDUAL":
                nm = " ".join(filter(None, (el.findtext(k) for k in ("FIRST_NAME", "SECOND_NAME", "THIRD_NAME"))))
            else:
                nm = el.findtext("FIRST_NAME") or ""
            if nm.strip():
                idx.add(nm, kind, "UN", prog)
            for al in el.iter("INDIVIDUAL_ALIAS" if tag == "INDIVIDUAL" else "ENTITY_ALIAS"):
                a = (al.findtext("ALIAS_NAME") or "").strip()
                if a:
                    idx.add(a, kind, "UN", prog)


def parse_eu(csv_bytes, idx):
    txt = csv_bytes.decode("utf-8-sig", "replace")
    rd = csv.DictReader(io.StringIO(txt), delimiter=";")
    for r in rd:
        nm = (r.get("NameAlias_WholeName") or "").strip()
        if not nm:
            continue
        st = (r.get("Entity_SubjectType") or r.get("Entity_SubjectType_ClassificationCode") or "").lower()
        kind = "Individual" if st.startswith("p") else "Company"
        idx.add(nm, kind, "EU", r.get("Entity_Regulation_Programme") or "")


def build(log=print):
    idx = Index()
    for src, urls in SOURCES.items():
        try:
            if src == "OFAC":
                a = _get(urls["sdn"], log)
                if a:
                    parse_ofac(a, _get(urls["alt"], log), idx)
            elif src == "UN":
                a = _get(urls["xml"], log)
                if a:
                    parse_un(a, idx)
            else:
                a = _get(urls["csv"], log)
                if a:
                    parse_eu(a, idx)
        except Exception as exc:
            log(f"      {src} list could not be read ({type(exc).__name__}: {exc})")
    log("      official lists loaded: " + (", ".join(f"{k} {v:,} names" for k, v in idx.count.items()) or "none"))
    return idx


def find(idx, texts, imo=None):
    """Names on the official lists that appear in the given headlines."""
    found = {}
    if imo and imo in idx.imo:
        r = idx.imo[imo]
        found[(r["n"], r["l"])] = r
    for t in texts:
        tok = norm(t).split()
        for i in range(len(tok)):
            for n in range(min(MAXGRAM, len(tok) - i), 1, -1):
                for r in idx.names.get(tuple(tok[i:i + n]), ()):
                    found.setdefault((r["n"], r["l"]), r)
    merged = {}
    for r in found.values():
        k = norm(r["n"])
        m = merged.setdefault(k, {"n": r["n"], "t": r["t"], "l": [], "p": []})
        if r["l"] not in m["l"]:
            m["l"].append(r["l"])
        if r["p"] and r["p"] not in m["p"]:
            m["p"].append(r["p"])
    return [{"n": m["n"], "t": m["t"], "l": ", ".join(m["l"]), "p": "; ".join(m["p"])[:80]} for m in merged.values()]


def annotate(events, log=print):
    """Add e['listed'] to each event: official-list names found in its headlines."""
    try:
        idx = build(log)
    except Exception as exc:
        log(f"      official lists skipped ({type(exc).__name__}: {exc})")
        return 0
    if not idx.count:
        return 0
    hits = 0
    for e in events:
        e["listed"] = find(idx, e.get("titles") or [e.get("title_en") or e.get("title") or ""], e.get("imo"))
        hits += bool(e["listed"])
    log(f"      {hits} events name someone or something on an official list")
    return hits

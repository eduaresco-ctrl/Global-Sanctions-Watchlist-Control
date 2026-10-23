# -*- coding: utf-8 -*-
"""Extra countries, ports, straits and ship-to-ship (STS) hotspots that matter for sanctions-related seizures.

The base place list (lexicon.py / geo.py) was built for drug seizures. This module adds what it lacks (North Korea,
DR Congo, Central African Republic, oil terminals, straits, STS areas, sanctioned-country ports) and rebuilds the
matching expressions, so import it once before reading any article (extract.py does).
To add a place: add a row to PLACES below (display name, country, [aliases], lat, lon).
"""
import re
from . import lexicon as L
from . import geo

COUNTRIES = [
    # display, aliases, lat, lon
    ("North Korea", ["north korea", "north korean", "dprk", "d.p.r.k", "democratic people's republic of korea", "corea del norte",
                     "coree du nord", "coreia do norte", "nordkorea", "noordkorea", "северная корея", "северной кореи", "северной корее",
                     "كوريا الشمالية", "朝鲜", "北朝鮮", "kuzey kore"], 40.3, 127.5),
    ("DR Congo", ["dr congo", "d.r. congo", "drc", "democratic republic of the congo", "democratic republic of congo",
                  "congo-kinshasa", "rd congo", "rdc", "republica democratica del congo", "republique democratique du congo",
                  "kinshasa"], -2.9, 23.7),
    ("Central African Republic", ["central african republic", "republica centroafricana", "republique centrafricaine",
                                  "republica centro-africana", "bangui"], 6.6, 20.9),
]

# display, country, aliases, lat, lon
PLACES = [
    ("Kharg Island", "Iran", ["kharg island", "kharg terminal", "khark island"], 29.25, 50.32),
    ("Bandar Imam Khomeini", "Iran", ["bandar imam khomeini", "bandar-e imam khomeini"], 30.43, 49.08),
    ("Jask", "Iran", ["jask terminal", "port of jask", "jask port"], 25.64, 57.77),
    ("Bushehr", "Iran", ["bushehr", "bushehr port"], 28.97, 50.84),
    ("Chabahar", "Iran", ["chabahar"], 25.29, 60.64),
    ("Zahedan", "Iran", ["zahedan"], 29.50, 60.86),
    ("Fujairah", "United Arab Emirates", ["fujairah", "fujeirah"], 25.12, 56.34),
    ("Ras Tanura", "Saudi Arabia", ["ras tanura"], 26.64, 50.16),
    ("Strait of Hormuz", None, ["strait of hormuz", "hormuz strait", "straits of hormuz", "estrecho de ormuz", "detroit d'ormuz"], 26.57, 56.25),
    ("Gulf of Oman", None, ["gulf of oman", "golfo de oman"], 24.5, 58.5),
    ("Ust-Luga", "Russia", ["ust-luga", "ust luga", "ust'-luga"], 59.68, 28.40),
    ("Primorsk", "Russia", ["primorsk"], 60.36, 28.61),
    ("Vyborg", "Russia", ["vyborg"], 60.71, 28.75),
    ("Kaliningrad", "Russia", ["kaliningrad"], 54.71, 20.51),
    ("Nakhodka", "Russia", ["nakhodka"], 42.81, 132.87),
    ("Kozmino", "Russia", ["kozmino"], 42.73, 133.07),
    ("Taman", "Russia", ["taman port", "port of taman"], 45.21, 36.72),
    ("Kerch Strait", "Russia", ["kerch strait", "strait of kerch", "kerch"], 45.30, 36.60),
    ("Baltic Sea", None, ["baltic sea", "baltic", "mar baltico", "mer baltique", "ostsee", "балтийск"], 57.5, 19.5),
    ("Gulf of Finland", None, ["gulf of finland", "golfo de finlandia", "golfe de finlande"], 59.9, 26.0),
    ("Danish straits", "Denmark", ["danish straits", "danish straight", "great belt", "oresund", "orestad strait", "skagen"], 55.6, 11.0),
    ("English Channel", None, ["english channel", "la manche", "canal de la mancha", "kanal"], 50.2, -0.8),
    ("Black Sea", None, ["black sea", "mar negro", "mer noire", "schwarzes meer", "черное море", "чёрное море"], 43.5, 34.0),
    ("Mediterranean Sea", None, ["mediterranean sea", "mediterranean", "mediterraneo", "mediterranee"], 35.0, 18.0),
    ("Red Sea", None, ["red sea", "mar rojo", "mer rouge", "rotes meer"], 20.0, 38.5),
    ("Gulf of Aden", None, ["gulf of aden", "golfo de aden"], 12.5, 47.0),
    ("Suez Canal", "Egypt", ["suez canal", "canal de suez"], 30.5, 32.35),
    ("Bosphorus", "Turkey", ["bosphorus", "bosporus", "bosforo", "bosphore"], 41.12, 29.07),
    ("Laconian Gulf", "Greece", ["laconian gulf", "gulf of laconia", "laconikos"], 36.55, 22.75),
    ("Kalamata", "Greece", ["kalamata"], 37.03, 22.11),
    ("Eastern OPL (Johor)", "Malaysia", ["eastern opl", "off johor", "eastern outer port limit"], 1.60, 104.60),
    ("Strait of Malacca", None, ["strait of malacca", "malacca strait", "straits of malacca", "estrecho de malaca"], 3.0, 100.5),
    ("Ceyhan", "Turkey", ["ceyhan", "ceyhan terminal"], 36.88, 35.93),
    ("Aktau", "Kazakhstan", ["aktau"], 43.65, 51.15),
    ("Brest (Belarus)", "Belarus", ["brest-litovsk", "brest belarus", "brest, belarus", "brest border"], 52.10, 23.70),
    ("Malaszewicze", "Poland", ["malaszewicze", "malaschewitschi"], 52.03, 23.54),
    ("Minsk", "Belarus", ["minsk"], 53.90, 27.57),
    ("Yerevan", "Armenia", ["yerevan", "erevan"], 40.18, 44.51),
    ("Tbilisi", "Georgia", ["tbilisi"], 41.72, 44.79),
    ("Dalian", "China", ["dalian"], 38.91, 121.61),
    ("Zhoushan", "China", ["zhoushan"], 29.99, 122.21),
    ("Dongying", "China", ["dongying"], 37.43, 118.67),
    ("Rizhao", "China", ["rizhao"], 35.42, 119.53),
    ("Shandong ports", "China", ["shandong"], 36.4, 118.1),
    ("Pyongyang", "North Korea", ["pyongyang", "pyeongyang"], 39.04, 125.76),
    ("Nampo", "North Korea", ["nampo", "nampho"], 38.74, 125.41),
    ("Wonsan", "North Korea", ["wonsan"], 39.15, 127.44),
    ("Chongjin", "North Korea", ["chongjin", "chongjin port"], 41.80, 129.78),
    ("Rason", "North Korea", ["rason", "najin", "rajin"], 42.25, 130.30),
    ("Damascus", "Syria", ["damascus", "damasco", "damas"], 33.51, 36.29),
    ("Baniyas", "Syria", ["baniyas", "banias"], 35.18, 35.95),
    ("Hodeidah", "Yemen", ["hodeidah", "hodeida", "hudaydah", "al hudaydah"], 14.80, 42.95),
    ("Ras Isa", "Yemen", ["ras isa", "ras issa"], 15.25, 42.60),
    ("Sanaa", "Yemen", ["sanaa", "sana'a"], 15.35, 44.21),
    ("Tripoli (Libya)", "Libya", ["tripoli libya", "tripoli, libya", "port of tripoli"], 32.89, 13.19),
    ("Benghazi", "Libya", ["benghazi", "bengasi"], 32.12, 20.07),
    ("Misrata", "Libya", ["misrata", "misurata"], 32.38, 15.09),
    ("Zawiya", "Libya", ["zawiya", "zawiyah"], 32.76, 12.73),
    ("Bosaso", "Somalia", ["bosaso", "bossaso"], 11.28, 49.18),
    ("Kismayo", "Somalia", ["kismayo", "kismayu"], -0.36, 42.55),
    ("Mogadishu", "Somalia", ["mogadishu", "mogadiscio"], 2.05, 45.32),
    ("Port Sudan", "Sudan", ["port sudan"], 19.62, 37.22),
    ("Juba", "South Sudan", ["juba"], 4.85, 31.58),
    ("Goma", "DR Congo", ["goma"], -1.68, 29.22),
    ("Bukavu", "DR Congo", ["bukavu"], -2.50, 28.86),
    ("Entebbe", "Uganda", ["entebbe"], 0.05, 32.46),
    ("Bangui", "Central African Republic", ["bangui"], 4.36, 18.56),
    ("Port-au-Prince", "Haiti", ["port-au-prince", "port au prince", "puerto principe"], 18.54, -72.34),
    ("Yangon", "Myanmar", ["yangon", "rangoon"], 16.87, 96.20),
    ("Kabul", "Afghanistan", ["kabul"], 34.53, 69.17),
    ("Jose Terminal", "Venezuela", ["jose terminal", "jose port", "puerto jose"], 10.17, -64.90),
    ("Puerto La Cruz", "Venezuela", ["puerto la cruz"], 10.21, -64.63),
    ("Maracaibo", "Venezuela", ["maracaibo"], 10.65, -71.65),
    ("Mariel", "Cuba", ["mariel"], 23.0, -82.75),
    ("Matanzas", "Cuba", ["matanzas"], 23.05, -81.58),
    ("Tel Aviv", "Israel", ["tel aviv"], 32.08, 34.78),
    ("Gaza", "Israel", ["gaza strip"], 31.5, 34.45),
]


# adjectives used for the country that acts ("German customs", "Italian police") - used only to find who made the seizure
DEMONYMS = {
    "german": "Germany", "italian": "Italy", "estonian": "Estonia", "french": "France", "greek": "Greece", "finnish": "Finland", "dutch": "Netherlands",
    "british": "United Kingdom", "american": "United States", "indian": "India", "turkish": "Turkey", "swedish": "Sweden", "danish": "Denmark",
    "norwegian": "Norway", "polish": "Poland", "latvian": "Latvia", "lithuanian": "Lithuania", "spanish": "Spain", "portuguese": "Portugal",
    "belgian": "Belgium", "irish": "Ireland", "maltese": "Malta", "cypriot": "Cyprus", "romanian": "Romania", "bulgarian": "Bulgaria",
    "croatian": "Croatia", "japanese": "Japan", "south korean": "South Korea", "australian": "Australia", "canadian": "Canada", "indonesian": "Indonesia",
    "malaysian": "Malaysia", "thai": "Thailand", "philippine": "Philippines", "singaporean": "Singapore", "egyptian": "Egypt", "emirati": "United Arab Emirates",
    "saudi": "Saudi Arabia", "omani": "Oman", "kenyan": "Kenya", "somali": "Somalia", "libyan": "Libya", "ukrainian": "Ukraine", "georgian": "Georgia",
    "chinese": "China", "taiwanese": "Taiwan", "israeli": "Israel", "moroccan": "Morocco", "djiboutian": "Djibouti", "nigerian": "Nigeria",
    "south african": "South Africa", "brazilian": "Brazil", "colombian": "Colombia", "panamanian": "Panama", "mexican": "Mexico", "us": "United States",
    "u.s.": "United States", "uk": "United Kingdom", "u.k.": "United Kingdom", "eu": None,
}


def _install():
    for disp, aliases, lat, lon in COUNTRIES:
        for a in aliases:
            L.COUNTRY_ALIAS[L.norm(a)] = disp
        geo.COUNTRY.setdefault(disp, [lat, lon])
    for disp, ctry, aliases, lat, lon in PLACES:
        for a in aliases:
            n = L.norm(a)
            if re.search(r"[Ѐ-ӿ]", n):         # Cyrillic aliases are handled by the stem matcher; skip
                continue
            L.PLACE_ALIAS.setdefault(n, (disp, ctry))
        geo.PLACE.setdefault(disp, [lat, lon])
        if ctry:
            geo.COUNTRY.setdefault(ctry, geo.COUNTRY.get(ctry, [lat, lon]))
    L.COUNTRY_RX = re.compile(r"(?<![a-zऀ-ॿ])(?<!chanvre )(?<!hemp )(" + L._alt(L.COUNTRY_ALIAS) + r")(?![a-z؀-ۿऀ-ॿ])")
    L.PLACE_RX = re.compile(r"(?<![a-zऀ-ॿ])(" + L._alt(L.PLACE_ALIAS) + r")(?![a-z؀-ۿऀ-ॿ])")


_install()


def geo_payload():
    """Coordinates for the dashboard: {country: [lat, lon]} and {place: [lat, lon, country]}."""
    out_p = {}
    for disp, (d, c) in {k: v for k, v in L.PLACE_ALIAS.items()}.items():
        pass
    seen = {}
    for k, (d, c) in L.PLACE_ALIAS.items():
        if d in geo.PLACE and d not in seen:
            seen[d] = [*geo.PLACE[d], c]
    return {"c": {k: list(v) for k, v in geo.COUNTRY.items()}, "p": seen}

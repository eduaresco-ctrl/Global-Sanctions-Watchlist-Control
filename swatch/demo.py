# -*- coding: utf-8 -*-
"""Invented sample articles for the offline demo (python run_daily.py --demo). Every name, vessel and URL is made up."""
import datetime as dt

# (days ago, language, outlet, title, text, outlet country)
_ARTICLES = [
    (1, "en", "Demo Maritime News", "Navy boards shadow fleet tanker Aurora Star off Estonia over false flag",
     "The Panama-flagged tanker Aurora Star, IMO 9123456, left Primorsk, Russia with crude oil and was detained in the Gulf of Finland. "
     "Investigators said its AIS was switched off for days and that the flag registration was fraudulent. EU sanctions apply to its owner, a shell company.", "Estonia"),
    (1, "en", "Example Wire", "Estonian navy detains sanctioned tanker Aurora Star",
     "The sanctioned tanker Aurora Star IMO 9123456 was detained by the navy near Tallinn. Its cargo of crude oil was bound for Turkey.", "Estonia"),
    (2, "en", "Demo Customs Review", "German customs seize microchips and drone components bound for Russia via Kazakhstan",
     "Customs officers in Hamburg seized dual-use goods worth 3.2 million euros. The microchips and drone components were declared as washing machine parts "
     "and sent through a front company in Kazakhstan to Russia. Export controls under EU sanctions were breached.", "Germany"),
    (3, "en", "Example Wire", "US forfeits Iranian oil: 2 million barrels aboard tanker Blue Meridian worth $140 million",
     "The Justice Department said the tanker Blue Meridian carried Iranian crude from Kharg Island to Zhoushan, China. A ship-to-ship transfer took place off Malaysia. "
     "OFAC had sanctioned the IRGC network behind the shipment.", "United States"),
    (4, "en", "Demo Maritime News", "Italian police seize superyacht of sanctioned Russian oligarch in La Spezia",
     "The yacht, worth 150 million euros, belongs to a businessman on the EU sanctions list. Prosecutors ordered the seizure.", "Italy"),
    (5, "en", "Example Wire", "UN panel: arms embargo breached as navy seizes ship carrying rifles and ammunition off Benghazi",
     "The vessel Sea Falcon, flagged Comoros, was boarded by an EU naval force. Rifles and ammunition were found under a cover load. UN arms embargo on Libya.", "Libya"),
    (6, "en", "Demo Customs Review", "Customs in Dubai seize 12 tonnes of North Korean coal under UN sanctions",
     "The coal arrived from Nampo, North Korea, relabelled as Russian origin. UN Security Council sanctions on the DPRK ban the trade. Documents were forged.", "United Arab Emirates"),
    (8, "en", "Example Wire", "Finland seizes cargo ship Eastern Wave over sanctions on Russia",
     "Finnish customs detained the cargo ship Eastern Wave in Kotka (transshipment via Estonia) carrying machine tools bound for Russia, a breach of the EU export ban.", "Finland"),
    (9, "en", "Demo Maritime News", "US Navy intercepts dhow with Iranian missile components bound for Yemen in Gulf of Aden",
     "The US Navy seized missile components and drone parts from a dhow. The Houthi shipment broke UN Security Council resolution 2216.", "Yemen"),
    (12, "en", "Example Wire", "UK Border Force seizes luxury cars and watches linked to sanctioned Russian businessman",
     "HMRC and Border Force seized luxury cars and watches worth 2 million pounds at Felixstowe. The goods were bound for Moscow via Dubai and the UK has sanctioned the buyer.", "United Kingdom"),
    (15, "en", "Demo Customs Review", "Singapore customs detain shipment of semiconductors destined for Russia via Hong Kong",
     "Singapore Customs seized semiconductors under export controls. The consignment was mislabelled and routed through a shell company in Hong Kong.", "Singapore"),
    (20, "en", "Example Wire", "Greece detains tanker Orion Gale after ship-to-ship transfer with sanctioned Iranian vessel",
     "The tanker Orion Gale, Cameroon flag, was held at Kalamata after a ship-to-ship transfer in the Laconian Gulf. Its insurance had lapsed. Iran oil sanctions.", "Greece"),
    (24, "en", "Demo Maritime News", "France boards shadow fleet tanker in Atlantic; Boracay detained over false flag, sanctions",
     "The French navy boarded the tanker Boracay, which left Primorsk with Russian crude. IMO 9234567. The flag was fraudulent.", "France"),
    (27, "en", "Example Wire", "Turkey seizes Syrian-bound cargo of dual-use chemicals at Mersin port",
     "Customs seized chemical precursors for weapons bound for Syria under UN sanctions. The shipment from China was declared as fertiliser.", "Turkey"),
    (31, "en", "Demo Customs Review", "Netherlands customs in Rotterdam seize drone engines headed for Russia through Armenia",
     "Dutch customs seized drone engines, dual-use goods valued at 900,000 euros, bound for Russia via Armenia. EU sanctions.", "Netherlands"),
    (35, "en", "Example Wire", "Somalia: navy seizes dhow carrying charcoal in breach of UN embargo",
     "A dhow carrying 300 tonnes of charcoal from Kismayo to the Gulf was seized. UN charcoal ban on Somalia.", "Somalia"),
    (41, "en", "Demo Maritime News", "India detains sanctioned tanker Pacific Dawn at Mundra over shell company ownership",
     "The tanker Pacific Dawn carrying Russian diesel was detained in Mundra. EU and UK sanctions list its owner, a shell company.", "India"),
    (47, "en", "Example Wire", "Venezuela sanctions: US seizes tanker Caribe Spirit with 1 million barrels of crude",
     "The US Justice Department seized the tanker Caribe Spirit near Jose Terminal. The oil, worth $70 million, was bound for China via Malaysia.", "United States"),
    (52, "en", "Demo Customs Review", "Germany: Zoll beschlagnahmt Dual-Use-Güter für Russland am Hamburger Hafen",
     "Der Zoll beschlagnahmte in Hamburg Elektronik und Mikrochips, die über Kasachstan nach Russland gehen sollten. Sanktionen und Exportkontrollen.", "Germany"),
    (58, "en", "Example Wire", "Estonia detains tanker Kiwala in Gulf of Finland for lack of valid insurance",
     "The sanctioned tanker flagged Panama was carrying diesel from Ust-Luga. The Estonian navy detained the ship.", "Estonia"),
    (63, "en", "Demo Maritime News", "Eagle Trader tanker held in Greece again; Kalamata officials seize sanctioned crude",
     "The Eagle Trader, IMO 9345678, Gabon flag, was detained at Kalamata with Russian crude, a ship-to-ship transfer off Malta was reported.", "Greece"),
    # not relevant: must be ignored
    (2, "en", "Example Wire", "Police seize 500 kg of cocaine at Antwerp port", "Cocaine hidden in banana boxes. No sanctions involved.", "Belgium"),
    (3, "en", "Example Wire", "Club handed disciplinary sanction after football match", "A fine and a ban from the stadium; the referee seized control.", "Spain"),
    (4, "en", "Example Wire", "US announces new sanctions on Iranian oil network", "The Treasury designated 20 tankers. No cargo was seized.", "United States"),
]


def demo_articles(today=None):
    today = today or dt.date.today()
    out = []
    for n, (ago, lang, outlet, title, text, ctry) in enumerate(_ARTICLES):
        out.append({"url": f"https://example.org/demo/{n}", "title": title, "text": text, "snippet": text[:200], "source": outlet,
                    "published": (today - dt.timedelta(days=ago)).isoformat(), "lang": lang, "source_country": ctry, "text_mode": "full"})
    return out

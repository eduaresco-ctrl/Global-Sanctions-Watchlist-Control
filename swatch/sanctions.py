# -*- coding: utf-8 -*-
"""Word lists for sanctions-related seizures. All patterns run on text that went through lexicon.norm()
(lower case, accents removed). Add a word here and it is used everywhere.

Three things must be in a report for it to count:
  1. a SANCTIONS cue          (sanctions, embargo, export controls, dual-use, shadow fleet, OFAC ...)
  2. a SEIZURE cue            (seized, detained, confiscated, impounded, intercepted ...)
  3. something that was seized (a vessel, oil, dual-use goods, weapons, luxury goods, cash, minerals ...)
"""
import re
from .lexicon import rx

# ---------------------------------------------------------------- 1. sanctions cue
SANCTIONS = rx(
    r"sanction", r"embargo", r"export\s+(?:control|ban|restriction|licen[cs]e)", r"dual[- ]use", r"doble\s+uso", r"double\s+usage",
    r"shadow\s+fleet", r"dark\s+fleet", r"ghost\s+fleet", r"flota\s+(?:fantasma|en\s+la\s+sombra)", r"flotte\s+(?:fantome|de\s+l'ombre)",
    r"schattenflotte", r"schaduwvloot", r"\bofac\b", r"specially\s+designated", r"\bsdn\b", r"entity\s+list", r"blacklist",
    r"price\s+cap", r"restricted\s+(?:goods|items|technolog)", r"prohibited\s+(?:to|for)\s+export", r"sancion", r"sancao", r"sancoes",
    r"sanzion", r"sanctie", r"sanktion", r"unsc\b", r"security\s+council\s+resolution", r"proliferation",
    r"\bban(?:ned)?\s+(?:on\s+)?(?:exports?|imports?)\b", r"circumvent", r"evad(?:e|ing|ed)\s+(?:the\s+)?(?:sanctions|embargo)",
    "санкц", "теневой флот", "теневого флота", "эмбарго", "двойного назначения", "عقوبات", "العقوبات", "حظر الأسلحة", "حظر التصدير", "اسطول الظل", "أسطول الظل",
    "制裁", "禁运", "禁運", "影子舰队", "影子艦隊", "两用", "yaptirim", "ambargo", "golge filo", "cift kullanimli", "प्रतिबंध")

# ---------------------------------------------------------------- 2. seizure cue
SEIZURE = rx(
    r"seiz", r"\bfroze\b", r"\bfrozen\b", r"\bfreez(?:e|es|ing)\b(?=.{0,60}(?:assets?|villa|property|properties|real\s+estate|shares|yacht|account|funds|aircraft|jet))", r"confiscat", r"impound", r"intercept", r"detain(?:ed|s|ing)?\b", r"\bheld\b(?=.{0,40}(?:port|tanker|vessel|ship|cargo))", r"\b(?:impound|seiz)\w*",
    r"(?:vessel|ship|tanker|cargo|shipment|consignment|goods|aircraft|plane|yacht)\s+(?:was|were|has\s+been|have\s+been)?\s*detained",
    r"board(?:s|ed|ing)?\b(?=.{0,60}(?:vessel|ship|tanker|cargo|dhow|boat|freighter))", r"forfeit", r"\bheld\s+(?:at|in)\s+port", r"blocked\s+(?:shipment|cargo|export|delivery)", r"stopped\s+(?:shipment|cargo|export)",
    r"\bbust(?:ed)?\b", r"\bhaul\b", r"\bcaptur(?:e|ed|es)\b(?=.{0,40}(?:tanker|vessel|ship|cargo))",
    r"arrest(?:ed)?\s+(?:the\s+)?(?:tanker|vessel|ship)", r"incaut", r"decomis", r"retenu", r"saisi", r"saisie", r"immobilis",
    r"apreen", r"retid[oa]", r"retencion", r"retuvo", r"beslag", r"aangehouden", r"beschlagnahm", r"sequestr",
    "задержан", "задержал", "арестован", "арестовал", "конфиск", "изъят", "ضبط", "احتجاز", "احتجز", "صادر", "مصادرة", "حجز",
    "扣押", "查扣", "没收", "沒收", "扣留", "el koy", "gozalt", "musadere", "alikoy")

# ---------------------------------------------------------------- 3. what was seized (category -> pattern, in priority order)
CAT_VESSEL = "Vessel / tanker"
CAT_OIL = "Oil & fuel"
CAT_DUAL = "Dual-use & military technology"
CAT_ARMS = "Weapons & ammunition"
CAT_WMD = "Chemicals & WMD-related items"
CAT_LUX = "Luxury goods & yachts"
CAT_AIR = "Aircraft & aviation"
CAT_PROP = "Real estate & company assets"
CAT_CULT = "Cultural property & antiquities"
CAT_FOOD = "Food, fertiliser & fisheries"
CAT_ASSET = "Cash, crypto & financial assets"
CAT_METAL = "Metals, minerals & commodities"
CAT_VEH = "Vehicles & machinery"
CAT_OTHER = "Other sanctioned goods"

_VNOUN_LAT = (r"tankers?|vessels?|ships?|cargo\s+ships?|bulk\s+carriers?|freighters?|petroleros?|buques?|barcos?|navires?|petroliers?|navios?|schip|schiff\w*|tanker\w*|gemi\w*")
_VNOUN_OTHER = ("танкер\\w*|судн\\w*|судно|судна|корабл\\w*|ناقلة|سفينة|سفن|油轮|油輪|船舶|货轮|貨輪|轮船")
VESSEL_RX = rx(r"(?<![a-z])(?:" + _VNOUN_LAT + r")(?![a-z])", _VNOUN_OTHER)

ITEMS = [
    (CAT_ASSET, "Crypto wallets, exchanges & servers", rx(r"crypto(?:currency)?\s+(?:wallets?|exchanges?|platforms?|mixers?|addresses)", r"(?:wallets?|addresses)\b(?=.{0,30}(?:crypto|bitcoin|usdt|tether|ethereum|seiz|frozen))", r"mining\s+(?:rigs?|farms?|machines?)", r"(?:crypto|exchange)\s+(?:servers?|domains?)", r"garantex", r"grinex")),
    # (category, label, pattern)   -- first match in this order names the item
    (CAT_WMD, "Nuclear / missile-related items", rx(r"centrifuge", r"maraging", r"uranium", r"nuclear[- ](?:related|material|component|equipment)", r"ballistic\s+missile\s+(?:propellant|fuel)", r"propellant", r"proliferation[- ]sensitive", r"\bwmd\b", r"weapons\s+of\s+mass\s+destruction")),
    (CAT_WMD, "Chemicals / precursors", rx(r"chemical\s+(?:weapon|precursor|agent)s?", r"nerve\s+agent", r"sodium\s+perchlorate", r"ammonium\s+perchlorate", r"precursors?\s+for\s+(?:weapons|missiles)")),
    (CAT_DUAL, "Missile / drone / nuclear components", rx(r"(?:components?|parts|engines?|guidance|electronics|navigation|equipment)\s+(?:for|of|used\s+in|destined\s+for)\s+(?:ballistic\s+)?(?:missiles?|drones?|uavs?|centrifuges?|nuclear)", r"missile\s+(?:parts?|components?|guidance|engines?)", r"procurement\s+network", r"proliferation\s+network")),
    (CAT_ARMS, "Missiles / rockets", rx(r"missiles?", r"missile\s+(?:part|component|propellant|technolog)\w*", r"rockets?\b", r"misiles?", r"ракет", "صواريخ", "صاروخ", "导弹", "飞弹")),
    (CAT_ARMS, "Drones / UAVs (military)", rx(r"military\s+drones?", r"attack\s+drones?", r"kamikaze\s+drones?", r"shahed", r"suicide\s+drones?", r"\buavs?\b(?=.{0,40}(?:iran|russia|houthi|military))")),
    (CAT_ARMS, "Firearms / small arms", rx(r"rifles?", r"assault\s+rifles?", r"kalashnikov", r"\bak-?47s?\b", r"machine\s+guns?", r"pistols?", r"firearms?", r"small\s+arms", r"\barms\b", r"weapons?", r"armas\b", r"armes\b", "оружи", "أسلحة", "سلاح", "武器", "军火", "軍火")),
    (CAT_ARMS, "Ammunition / explosives", rx(r"ammunition", r"\bammo\b", r"rounds\s+of", r"cartridges", r"explosives?", r"detonators?", r"munitions?", r"grenades?", r"rpgs?\b", r"anti-?tank", r"боеприпас", "ذخيرة", "ذخائر", "弹药", "彈藥")),
    (CAT_ARMS, "Military equipment", rx(r"military\s+(?:equipment|hardware|goods|material|cargo|supplies)", r"body\s+armou?r", r"armou?red\s+vehicles?", r"tanks?\b(?=.{0,30}(?:military|army|battle))", r"artillery", r"радиолокац")),
    (CAT_DUAL, "Microchips / semiconductors", rx(r"micro-?chips?", r"semi-?conductors?", r"integrated\s+circuits?", r"\bchips?\b(?=.{0,40}(?:russia|iran|export|sanction|dual|military|electronic))", r"\bfpga\b", r"микросхем", "芯片", "半导体", "半導體")),
    (CAT_AIR, "Aircraft parts & engines", rx(r"aircraft\s+(?:parts?|components?|engines?|spares?)", r"aviation\s+(?:parts?|spares?|components?)", r"(?:boeing|airbus)\s+(?:parts?|spares?)", r"airplane\s+parts?", r"helicopter\s+(?:parts?|spares?)", r"jet\s+engines?", r"turbo-?(?:jet|fan)", r"avionics", r"spare\s+parts\s+for\s+(?:aircraft|airplanes?|planes?)")),
    (CAT_DUAL, "Drone / aircraft components", rx(r"drone\s+(?:parts?|components?|engines?)", r"uav\s+(?:parts?|components?)", r"aircraft\s+(?:parts?|components?|engines?)", r"aviation\s+parts?", r"helicopter\s+parts?", r"jet\s+engines?", r"turbo-?jet", r"gas\s+turbines?")),
    (CAT_DUAL, "Surveillance & telecom equipment", rx(r"surveillance\s+(?:equipment|technolog|system|software)", r"spyware", r"interception\s+(?:equipment|technolog|system)", r"\bimsi\b", r"facial\s+recognition", r"telecom\w*\s+equipment", r"telecommunications?\s+equipment", r"jamming\s+(?:equipment|devices?)")),
    (CAT_DUAL, "Electronics / navigation / radar", rx(r"electronic\s+(?:components?|equipment|parts)", r"radar", r"night[- ]vision", r"thermal\s+(?:imag|camera|scope|sight)", r"\bgps\b", r"navigation\s+(?:equipment|system)", r"telecom\w*\s+equipment", r"optical\s+(?:equipment|sight)", r"lasers?\b", r"encryption", r"servers?\b(?=.{0,30}(?:export|sanction|russia))", r"electronique")),
    (CAT_DUAL, "Machine tools / CNC", rx(r"machine\s+tools?", r"\bcnc\b", r"lathes?", r"milling\s+machines?", r"industrial\s+machinery", r"станк", "机床")),
    (CAT_DUAL, "Dual-use goods (unspecified)", rx(r"dual[- ]use", r"doble\s+uso", r"double\s+usage", r"двойного\s+назначения", "两用", r"cift\s+kullanimli", r"controlled\s+(?:goods|items|technolog)", r"export[- ]controlled", r"restricted\s+(?:goods|items|technolog)")),
    (CAT_OIL, "Crude oil", rx(r"crude(?:\s+oil)?", r"\boil\b", r"petroleo", r"petrole\b", r"nefte", r"нефт", "نفط", "النفط", "石油", "原油", "petrol\b", r"barrels?", r"bbls?")),
    (CAT_OIL, "Refined fuel / diesel / LNG", rx(r"diesel", r"gas-?oil", r"gasoil", r"gasoline", r"\bpetrol\b", r"jet\s+fuel", r"kerosene", r"fuel\s+oil", r"\bfuel\b", r"refined\s+(?:product|petroleum|oil)", r"\blng\b", r"\blpg\b", r"naphtha", r"bunker\s+fuel", r"combustible", r"carburant", "топлив", "дизел", "وقود", "燃油", "柴油", "akaryakit", "mazot")),
    (CAT_FOOD, "Seafood / fish", rx(r"seafood", r"\bfish\b", r"\bsquid\b", r"\bcrabs?\b", r"fishing\s+(?:catch|products?)", r"fish\s+(?:cargo|shipment)")),
    (CAT_FOOD, "Fertiliser", rx(r"fertili[sz]ers?", r"potash", r"ammonium\s+nitrate")),
    (CAT_FOOD, "Grain / food / agricultural products", rx(r"\bgrain\b", r"\bwheat\b", r"\bcorn\b", r"\bbarley\b", r"\bsugar\b", r"\bfood\b", r"agricultural\s+products?", r"sunflower\s+oil", r"\brice\b", r"stolen\s+ukrainian\s+grain")),
    (CAT_LUX, "Yacht / boat", rx(r"\byachts?\b", r"superyachts?", r"мегаяхт", "яхт", "يخت", "游艇", "遊艇")),
    (CAT_AIR, "Aircraft (jets, airliners, helicopters)", rx(r"private\s+(?:jet|plane|aircraft)", r"business\s+jet", r"\bjets?\b(?=.{0,30}(?:oligarch|sanction|seiz|private))", r"airliners?", r"boeing\s+\d{3}", r"airbus\s+a\d{3}", r"aircraft\b(?=.{0,30}(?:seiz|sanction|oligarch))", r"helicopters?\b(?=.{0,30}(?:seiz|sanction|oligarch))")),
    (CAT_CULT, "Antiquities & cultural property", rx(r"antiquit(?:y|ies)", r"artefacts?", r"artifacts?", r"archaeological", r"cultural\s+(?:property|heritage|objects?|goods)", r"looted", r"manuscripts?", r"mosaics?", r"antigüedades|antiquites|antikvit", "древност", "文物", "آثار")),
    (CAT_PROP, "Real estate", rx(r"real\s+estate", r"\bvillas?\b(?=.{0,40}(?:seiz|sanction|oligarch|frozen|freez))", r"mansions?", r"\bapartments?\b(?=.{0,40}(?:seiz|sanction|oligarch|frozen|freez))", r"properties\b(?=.{0,40}(?:seiz|sanction|oligarch|frozen|freez))", r"\bproperty\b(?=.{0,40}(?:seiz|sanction|oligarch|frozen|freez))", r"residences?\b(?=.{0,40}(?:seiz|sanction|oligarch|frozen|freez))", "недвижимост")),
    (CAT_PROP, "Company shares & holdings", rx(r"(?:company|corporate)\s+(?:shares|stakes?|assets|holdings)", r"\bshares\b(?=.{0,40}(?:seiz|sanction|oligarch|frozen|freez))", r"\bstakes?\b(?=.{0,40}(?:seiz|sanction|oligarch|frozen|freez))", r"shareholdings?", r"\bsubsidiar(?:y|ies)\b(?=.{0,40}(?:seiz|sanction|frozen|freez|nationali[sz]))", r"nationali[sz]ed\s+(?:company|assets)", r"доли\b")),
    (CAT_LUX, "Art & collectibles", rx(r"artworks?", r"paintings?", r"\bart\s+collection", r"sculptures?", r"collectibles?", r"\bart\b(?=.{0,30}(?:seiz|sanction|oligarch))")),
    (CAT_OTHER, "Tobacco & alcohol", rx(r"cigarettes?", r"tobacco", r"\bvodka\b", r"\balcohol\b", r"\bwine\b", r"\bspirits\b(?=.{0,30}(?:seiz|sanction|smuggl))", r"\bbeer\b")),
    (CAT_LUX, "Luxury goods (cars, watches, art, jewellery, alcohol)", rx(r"luxury\s+(?:goods?|items?|cars?|vehicles?|products?|watches)", r"supercars?", r"\bferrari", r"lamborghini", r"rolls[- ]royce", r"bentley", r"watches", r"jewel(?:l)?ery", r"artworks?", r"paintings?", r"\bart\s+collection", r"champagne", r"whisk(?:e)?y", r"cognac", r"designer\s+(?:goods|clothes|handbags)", r"handbags?")),
    (CAT_ASSET, "Cash / bank accounts", rx(r"\bcash\b", r"bank\s+accounts?", r"bank\s+funds", r"\bfunds\b(?=.{0,30}(?:seiz|sanction|frozen))", r"foreign\s+currency", r"banknotes", r"money\s+transfers?", r"\bassets?\b(?=.{0,30}(?:seiz|sanction|oligarch|frozen))", r"efectivo", r"especes", "наличн", "активы", "资产")),
    (CAT_ASSET, "Cryptocurrency", rx(r"crypto(?:currency|currencies)?", r"bitcoin", r"\busdt\b", r"tether", r"\bethereum\b", r"крипто", "加密货币", "加密貨幣")),
    (CAT_METAL, "Gold / diamonds / precious metals", rx(r"\bgold\b", r"diamonds?", r"precious\s+(?:metals?|stones?)", r"\boro\b", r"золот", "ذهب", "黄金", "黃金", "altin")),
    (CAT_METAL, "Coal", rx(r"\bcoal\b", r"carbon\s+mineral", r"уголь", r"угл", "فحم", "煤炭", "komur")),
    (CAT_METAL, "Charcoal", rx(r"charcoal", r"carbon\s+vegetal", r"charbon\s+de\s+bois")),
    (CAT_METAL, "Steel / iron / copper / aluminium", rx(r"\bsteel\b", r"\biron\b", r"iron\s+ore", r"copper", r"alumin(?:i)?um", r"\bnickel\b", r"\btitanium\b", r"scrap\s+metal", r"pig\s+iron", r"\bmetals?\b", r"\bores?\b", r"минерал", "钢铁", "钢材")),
    (CAT_METAL, "Timber / wood", rx(r"\btimber\b", r"\blumber\b", r"\bwood\b", r"\blogs\b", r"plywood")),
    (CAT_VEH, "Vehicles", rx(r"\bcars?\b", r"\btrucks?\b", r"\blorr(?:y|ies)\b", r"vehicles?", r"automobiles?", r"\bsuvs?\b", r"motorcycles?", r"automoviles?", r"voitures?", r"carros?", r"автомобил", r"машин", "سيارات", "汽车", "汽車", "araclar", "arac")),
    (CAT_VEH, "Machinery / heavy equipment", rx(r"machinery", r"heavy\s+equipment", r"excavators?", r"bulldozers?", r"generators?", r"engines?\b", r"turbines?", r"\bequipment\b", r"spare\s+parts", r"auto\s+parts", r"оборудован", "معدات", "设备", "設備")),
    (CAT_OTHER, "Textiles / consumer goods", rx(r"textiles?", r"garments?", r"clothing", r"consumer\s+goods", r"electronics", r"appliances", r"cosmetics", r"cigarettes", r"tobacco", r"alcohol", r"vodka", r"pharmaceuticals?", r"medicines?")),
]
VESSEL_ITEM = "Vessel / tanker seized"

# a seized thing is the vessel itself when the seizure verb sits near a vessel noun in the headline
_VERB = (r"(?:seiz\w*|detain\w*|impound\w*|intercept\w*|board\w*|arrest\w*|captur\w*|confiscat\w*|stop\w*|block\w*|hold\w*|held|forfeit\w*|detuvo|retuvo|retenu\w*|saisi\w*|immobilis\w*|incaut\w*|"
         r"apreend\w*|beslag\w*|aangehouden|beschlagnahm\w*|festgesetzt|задержа\w*|арестова\w*|захват\w*|احتجز\w*|ضبط\w*|扣押|扣留|el\s+koy\w*|gozalt\w*|alikon\w*)")
_VN = r"(?<![a-z])(?:" + _VNOUN_LAT + r")(?![a-z])|" + _VNOUN_OTHER
VESSEL_SEIZED_RX = rx(_VERB + r"[^.]{0,50}?(?:" + _VN + r")", r"(?:" + _VN + r")[^.]{0,40}?" + _VERB)

# ---------------------------------------------------------------- regimes (sanctions programmes)
REGIMES = {
    "Russia / Ukraine-related": rx(r"russia", r"russian", r"kremlin", r"oligarch", r"moscow", r"ukrain", r"crimea", r"donbas", r"putin", r"price\s+cap", r"rusia", r"russie", r"russland", r"россия", r"росси", r"российск", "روسيا", "俄罗斯", "俄羅斯", "rusya", r"belarus", r"lukashenko", "беларус"),
    "Iran": rx(r"\biran", r"tehran", r"irgc", r"revolutionary\s+guard", r"islamic\s+republic", r"\birani", r"iran\w*\s+oil", "иран", "ايران", "إيران", "伊朗", "iran\b", r"hormuz", r"kharg"),
    "North Korea (DPRK)": rx(r"north\s+korea", r"\bdprk\b", r"pyongyang", r"kim\s+jong", r"1718", r"corea\s+del\s+norte", r"coree\s+du\s+nord", r"северн\w+\s+коре", "كوريا الشمالية", "朝鲜", "北朝鮮"),
    "Syria": rx(r"\bsyria", r"damascus", r"assad", r"\bsiria", r"syrie", "сири", "سوريا", "叙利亚", "suriye"),
    "Venezuela": rx(r"venezuela", r"maduro", r"pdvsa", "венесуэл", "فنزويلا", "委内瑞拉"),
    "Yemen / Houthis": rx(r"houthi", r"huthi", r"ansar\s+allah", r"yemen", r"hodeidah", r"hudaydah", "الحوثي", "اليمن", "хуси", "胡塞"),
    "Libya": rx(r"libya", r"haftar", r"tripoli", r"benghazi", r"libia", r"libye", r"ливи", "ليبيا", "利比亚"),
    "Somalia / Al-Shabaab": rx(r"somalia", r"al-?shabaab", r"charcoal", r"somali", r"сомал", "الصومال", "索马里"),
    "Sudan / South Sudan": rx(r"sudan", r"khartoum", r"\brsf\b", r"rapid\s+support", r"судан", "السودان", "苏丹"),
    "DR Congo / Central Africa": rx(r"dr\s+congo", r"democratic\s+republic\s+of\s+(?:the\s+)?congo", r"\bm23\b", r"\bdrc\b", r"central\s+african\s+republic", r"\bcar\b(?=.{0,20}(?:embargo|sanction))", "конго"),
    "Mali / Sahel": rx(r"\bmali\b", r"sahel", r"wagner", r"africa\s+corps", r"\bmali\b"),
    "Haiti": rx(r"haiti", r"port-?au-?prince", r"haitian"),
    "Myanmar": rx(r"myanmar", r"burma", r"tatmadaw", r"junta", "мьянм", "缅甸"),
    "Afghanistan / Taliban": rx(r"taliban", r"afghanistan", r"афганистан", "طالبان"),
    "Counter-terrorism (ISIL / Al-Qaida / Hezbollah / Hamas)": rx(r"isil", r"\bisis\b", r"islamic\s+state", r"al-?qa'?ida", r"hezbollah", r"hizbollah", r"\bhamas\b", r"terror(?:ist)?\s+financ", r"daesh", "حزب الله", "حماس"),
    "Cuba (US embargo)": rx(r"\bcuba", r"havana", "куба", "كوبا", "古巴"),
    "Nicaragua / Zimbabwe / other": rx(r"nicaragua", r"zimbabwe", r"eritrea", r"south\s+sudan", r"lebanon", r"iraq"),
}

AUTHORITIES = {
    "UN": rx(r"united\s+nations", r"\bun\s+(?:security\s+council|sanctions|panel|resolution|embargo|committee)", r"\bunsc\b", r"security\s+council", r"\bun\b\s+panel", r"resolution\s+(?:1718|1737|1970|2231|2127|2653|2216|2713)", r"1718\s+committee", "оон", "联合国", "聯合國"),
    "EU": rx(r"european\s+union", r"\beu\b", r"eu-sanction", r"eu\s+(?:sanctions|council|embargo|package)", r"brussels", r"unione\s+europea", r"union\s+europeenne", r"евросоюз", "الاتحاد الأوروبي", "欧盟", "歐盟", r"\b\d{1,2}(?:st|nd|rd|th)\s+(?:sanctions\s+)?package"),
    "US": rx(r"\bofac\b", r"u\.?s\.?\s+(?:sanctions|treasury|department|commerce|navy|coast\s+guard|justice|customs|embargo)", r"treasury\s+department", r"\bdoj\b", r"department\s+of\s+justice", r"\bbis\b", r"commerce\s+department", r"american\s+sanctions", r"washington", r"united\s+states", r"\bus-sanction", r"u\.s\.-sanction", r"\bhsi\b", r"homeland\s+security", r"сша", "الولايات المتحدة", "美国", "美國", r"\bsdn\b"),
    "UK": rx(r"\bofsi\b", r"\bhmrc\b", r"uk\s+(?:sanctions|government|treasury|border\s+force)", r"british\s+(?:sanctions|government)", r"\bfcdo\b", r"\bohle?\b", r"border\s+force", r"london", r"\buk-sanction", r"britain", r"великобритани"),
    "Other (Japan, Canada, Australia, Switzerland...)": rx(r"japan(?:ese)?\s+(?:sanctions|government|coast)", r"canad(?:a|ian)\s+(?:sanctions|government)", r"australia(?:n)?\s+(?:sanctions|government)", r"swiss\s+(?:sanctions|government)", r"seco\b", r"south\s+korea(?:n)?\s+(?:sanctions|government|coast)", r"new\s+zealand\s+sanctions"),
}

AGENCIES = {
    "Customs / border": rx(r"customs", r"border\s+(?:force|guard|agency|control)", r"aduana", r"douane", r"zoll", r"alfandega", "таможн", "الجمارك", "海关", "海關", "gumruk", r"hmrc", r"cbp\b", r"\bcbsa\b"),
    "Coast guard / navy": rx(r"coast\s*guard", r"navy", r"naval", r"marine", r"guardia\s+costera", r"garde[- ]cotes", r"kustwacht", r"guarda\s+costeira", r"береговой", "خفر السواحل", "海警", r"sahil\s+guvenlik", r"warship", r"frigate"),
    "Police / prosecutors / courts": rx(r"police", r"prosecut", r"\bcourt\b", r"judge", r"magistrate", r"attorney", r"public\s+prosecutor", r"fiscalia", r"parquet", r"staatsanwalt", r"polizei", r"policia", "полици", "прокурор", "суд\b", "الشرطة", "النيابة", "警方", "检察"),
    "Justice / Treasury / Commerce departments": rx(r"department\s+of\s+(?:justice|commerce|treasury)", r"treasury", r"\bdoj\b", r"\bofac\b", r"\bbis\b", r"ministry\s+of\s+(?:finance|justice|defen[cs]e)", r"\bhsi\b", r"homeland\s+security", r"export\s+enforcement"),
}

# ---------------------------------------------------------------- evasion indicators (phrases in the article, never traits of a person)
INDICATORS = {
    "ais_dark": rx(r"\bais\b[^.]{0,40}(?:off|dark|disabled|switched|turned|spoof|manipulat|gap|transponder)", r"(?:disabled|switched\s+off|turned\s+off|spoofed?|manipulated)\s+(?:its\s+|their\s+|the\s+)?(?:ais|transponder|tracking)",
                   r"transponder", r"going\s+dark", r"went\s+dark", r"dark\s+activity", r"gps\s+spoof", r"tracking\s+(?:system|device)s?\s+(?:off|disabled)", r"without\s+(?:ais|a\s+transponder)", r"sin\s+ais",),
    "sts_transfer": rx(r"ship[- ]to[- ]ship", r"\bsts\b", r"transfer(?:red|s|ring)?\s+(?:the\s+)?(?:cargo|oil|crude|fuel)\s+(?:at\s+sea|offshore|to\s+another)", r"transshipp?ed\s+at\s+sea", r"offshore\s+transfer",
                       r"transbordo\s+en\s+(?:alta\s+mar|el\s+mar)", r"transbordement\s+en\s+mer", r"перегруз"),
    "false_flag": rx(r"false\s+flag", r"fake\s+flag", r"fraudulent(?:ly)?\s+(?:flag|regist)", r"flag\s+(?:hopping|swap|switch)", r"re-?flag", r"changed\s+(?:its\s+|their\s+)?flag", r"\bstateless\b",
                     r"without\s+(?:a\s+)?(?:valid\s+)?(?:flag|registration|registry)", r"flag\s+of\s+convenience", r"fraudulently\s+registered", r"unregistered\s+(?:vessel|tanker|ship)", r"bandera\s+falsa", r"faux\s+pavillon",
                     r"\bflag\b[^.]{0,40}(?:fraudulent|fake|invalid|not\s+registered|deregistered)", r"fraudulent\s+(?:registry|registration)"),
    "front_company": rx(r"shell\s+compan", r"front\s+compan", r"straw\s+(?:compan|man)", r"letterbox", r"newly\s+(?:registered|created|formed|incorporated|established)\s+(?:compan|firm|entit)", r"opaque\s+(?:ownership|structure)", r"nominee",
                        r"mailbox\s+compan", r"intermediary\s+compan", r"sociedad\s+pantalla", r"societe\s+ecran", r"empresa\s+fantasma", r"подставн", r"фирм\w*-однодневк", r"front\s+firm"),
    "third_country": rx(r"re-?export", r"transship", r"trans-?shipment", r"third[- ]countr", r"via\s+(?:an?\s+)?(?:intermediary|third)", r"intermediar(?:y|ies)\s+countr", r"diverted\s+(?:via|through|to)", r"circumvent", r"evad(?:e|ing|ed)\s+(?:the\s+)?(?:sanctions|embargo)", r"sanctions[- ]evasion", r"sanctions[- ]busting", r"parallel\s+import", r"reexport", r"реэкспорт", r"параллельн\w+\s+импорт"),
    "false_declaration": rx(r"mislabel", r"mis-?declar", r"falsely\s+declared", r"false\s+(?:declaration|customs\s+declaration|description|invoice|certificate|documents?)", r"declared\s+as", r"forged\s+(?:documents?|certificates?|invoices?|papers?|licen[cs]es?)", r"falsified", r"fake\s+(?:invoices?|certificates?|documents?|papers?|licen[cs]es?)", r"wrong\s+(?:hs|customs)\s+code", r"false\s+hs\s+code", r"disguised\s+as", r"undervalu", r"fraudulent\s+(?:documents?|invoices?|licen[cs]es?)", r"falsa\s+declaracion", r"fausse\s+declaration", r"фальсифиц", r"поддельн"),
    "concealment": rx(r"hidden\s+(?:in|inside|among|behind)", r"concealed", r"false\s+compartment", r"secret\s+compartment", r"camouflag", r"smuggl", r"contraband", r"undeclared", r"oculto", r"dissimul"),
    "name_change": rx(r"renamed", r"changed\s+(?:its\s+|their\s+|the\s+)?name", r"name\s+change", r"new\s+name", r"repainted", r"changed\s+owner", r"change\s+of\s+ownership", r"sold\s+(?:several\s+times|repeatedly)"),
    "insurance": rx(r"fake\s+insurance", r"lack\s+of\s+(?:valid\s+)?insurance", r"(?:invalid|false)\s+insurance", r"fraudulent\s+insurance", r"no\s+(?:valid\s+)?insurance", r"uninsured", r"without\s+(?:valid\s+)?insurance", r"unknown\s+insur", r"insurance\s+(?:lapsed|expired|certificate)", r"p&i\s+(?:cover|club)", r"sin\s+seguro"),
    "price_cap": rx(r"price\s+cap", r"above\s+the\s+cap", r"cap\s+of\s+\$", r"предельн\w+\s+цен"),
    "sanctioned_party": rx(r"sanctioned\s+(?:tankers?|vessels?|ships?|company|compan|entity|entities|individual|person|oligarch|businessman|businesswoman|owner|bank|exporter|shipper|importer|firm|operator|tycoon|network|buyer|supplier|manager)",
                           r"blacklisted", r"on\s+(?:the\s+)?(?:ofac|sdn|sanctions|entity|eu|un|uk)\s+(?:sanctions\s+)?list", r"ofac[- ]listed", r"(?:designated|listed)\s+by\s+(?:the\s+)?(?:u\.?s\.?|us|eu|uk|un|ofac|treasury)", r"sanctioned\s+by\s+the",
                           r"owned\s+by\s+(?:a\s+)?sanctioned", r"linked\s+to\s+(?:a\s+)?sanctioned", r"sancionad[oa]", r"sanctionne", r"подсанкционн", r"находящ\w+\s+под\s+санкц", "被制裁", "受制裁", "制裁名单"),
    "intel_led": rx(r"intelligence[- ]led", r"acting\s+on\s+(?:a\s+)?tip", r"tip-?off", r"investigation\s+(?:by|into)", r"undercover", r"monitored\s+(?:the\s+)?(?:vessel|ship)", r"tracked\s+(?:the\s+)?(?:vessel|ship)", r"surveillance", r"informacion\s+de\s+inteligencia"),
}

# hubs that often appear as the declared destination or transit of diverted goods (a pointer for analysts, not a verdict on the country)
DIVERSION_HUBS = {"United Arab Emirates", "Turkey", "Kazakhstan", "Armenia", "Kyrgyzstan", "Georgia", "Hong Kong", "Uzbekistan",
                  "Tajikistan", "Serbia", "Belarus", "Malaysia", "Singapore", "Oman", "Azerbaijan", "Mongolia", "China", "India", "Egypt",
                  "Panama", "Cyprus", "Malta", "Greece", "Djibouti", "Bahrain", "Qatar", "Georgia"}
# countries that themselves carry a UN/EU/US sanctions programme (used to flag "origin or destination in a sanctioned jurisdiction")
SANCTIONED_JURISDICTIONS = {"Russia", "Iran", "North Korea", "Syria", "Venezuela", "Belarus", "Libya", "Yemen", "Somalia", "Sudan", "South Sudan",
                            "DR Congo", "Central African Republic", "Mali", "Haiti", "Myanmar", "Afghanistan", "Cuba", "Nicaragua", "Zimbabwe", "Eritrea", "Lebanon", "Iraq"}

# stories that mention sanctions and a seizure verb but are not about seized goods
EXCLUDE = rx(r"seiz\w*\s+(?:power|control|the\s+opportunity|the\s+day|the\s+moment|upon|on\s+the)", r"coup", r"disciplinary", r"\bfootball\b", r"\bsoccer\b", r"\bgolf\b", r"\bnba\b", r"\bnfl\b", r"fifa", r"uefa",
             r"\bstock\s+market\b", r"\bnetflix\b", r"\bmovie\b", r"\bseason\s+\d", r"video\s+game", r"\bepisode\b", r"school\s+(?:sanction|discipline)", r"sanctuary", r"\bsanctity\b",
             r"seizure\s+(?:disorder|medicine|medication|patients?|alert)", r"epilep", r"\bseizures?\b(?=.{0,20}(?:child|patient|hospital|dog|medical|brain))", r"legali[sz]", r"cannabis\s+(?:dispensar|shop)",
             r"drug\s+(?:seizure|bust|trafficking)(?!.{0,80}sanction)", r"narcotics?(?!.{0,80}sanction)")

# quantity words
UNIT_WORDS = {
    "barrels": rx(r"barrels?", r"bbls?", r"barriles", r"barils"),
    "tonnes": rx(r"tonnes?", r"tons?", r"toneladas?", r"metric\s+tons?", r"тонн"),
    "units": rx(r"units?", r"pieces?", r"items?", r"sets?", r"chips?", r"drones?", r"vehicles?", r"cars?", r"trucks?", r"rifles?", r"pistols?", r"missiles?", r"rounds", r"containers?", r"packages?", r"boxes", r"crates", r"pallets?"),
}

# a country that carries its own programme implies that regime when the text names no programme word
REGIME_OF_COUNTRY = {"Russia": "Russia / Ukraine-related", "Belarus": "Russia / Ukraine-related", "Iran": "Iran", "North Korea": "North Korea (DPRK)",
                     "Syria": "Syria", "Venezuela": "Venezuela", "Yemen": "Yemen / Houthis", "Libya": "Libya", "Somalia": "Somalia / Al-Shabaab",
                     "Sudan": "Sudan / South Sudan", "South Sudan": "Sudan / South Sudan", "DR Congo": "DR Congo / Central Africa",
                     "Central African Republic": "DR Congo / Central Africa", "Mali": "Mali / Sahel", "Haiti": "Haiti", "Myanmar": "Myanmar",
                     "Afghanistan": "Afghanistan / Taliban", "Cuba": "Cuba (US embargo)"}

FLAG_OF_CONCERN = {"Gabon", "Comoros", "Cameroon", "Palau", "Sierra Leone", "Togo", "Cook Islands", "Tanzania", "Benin", "Guinea-Bissau", "Eswatini",
                   "Sao Tome and Principe", "Mongolia", "Belize", "Guyana", "Djibouti"}   # registries often named in reports about false or fraudulent flags

# "No cargo was seized" and plain designation news
NEGATED_SEIZURE = rx(r"\bno\s+(?:cargo|goods|vessels?|ships?|oil|assets?|tankers?|shipments?|items?)\s+(?:was|were|has|have)\s+(?:been\s+)?(?:seiz|detain|confiscat|impound)",
                     r"\bnothing\s+(?:was|has\s+been)\s+(?:seiz|detain|confiscat)", r"\bnot\s+(?:been\s+)?(?:seized|detained|confiscated|impounded)\b")
DESIGNATION_TITLE = rx(r"^(?:\w+\s+){0,3}(?:announces?|imposes?|adopts?|unveils?|issues?|expands?|extends?|tightens?|designates?|lifts?|eases?|renews?|approves?)\s+(?:new\s+|fresh\s+|further\s+|additional\s+|more\s+)?sanctions?")

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from swatch import lists

SDN = b'''1,"SOVCOMFLOT PAO","-0- ","RUSSIA-EO14024","-0- ","-0- ","-0- ","-0- ","-0- ","-0- ","-0- ","-0- "
2,"SECHIN, Igor Ivanovich","individual","RUSSIA-EO14024","Deputy PM","-0- ","-0- ","-0- ","-0- ","-0- ","-0- ","DOB 1960"
3,"DF PEAK","vessel","IRAN","-0- ","-0- ","Crude Oil Tanker","-0- ","-0- ","Gabon","-0- ","Vessel Registration Identification IMO 9341067; MMSI 1"
4,"SUN","vessel","RUSSIA","-0- ","-0- ","-0- ","-0- ","-0- ","-0- ","-0- ","IMO 9293117"
'''
ALT = b'2,1,"aka","IGOR SECHIN","-0- "\n'
UN = b'<R><INDIVIDUALS><INDIVIDUAL><FIRST_NAME>Ali</FIRST_NAME><SECOND_NAME>Reza Karimi</SECOND_NAME><UN_LIST_TYPE>Iran</UN_LIST_TYPE></INDIVIDUAL></INDIVIDUALS><ENTITIES><ENTITY><FIRST_NAME>Blue Wave Shipping Company</FIRST_NAME><UN_LIST_TYPE>DPRK</UN_LIST_TYPE></ENTITY></ENTITIES></R>'
EU = b'Entity_LogicalId;NameAlias_WholeName;Entity_SubjectType\n1;Sinokor Merchant Marine Co;enterprise\n2;Viktor Petrov Orlov;person\n'


def make():
    idx = lists.Index()
    lists.parse_ofac(SDN, ALT, idx); lists.parse_un(UN, idx); lists.parse_eu(EU, idx)
    return idx


def test_names_and_imo():
    idx = make()
    r = lists.find(idx, ["Sovcomflot PAO tanker boarded", "Igor Ivanovich Sechin sanctioned"], imo="9341067")
    names = {x["n"] for x in r}
    assert "SOVCOMFLOT PAO" in names and "DF PEAK" in names
    assert any(x["t"] == "Individual" for x in r)


def test_single_word_never_matches():
    idx = make()
    assert lists.find(idx, ["The sun rose over the tanker"]) == []
    assert lists.find(idx, ["Tanker seized"], imo="9293117")  # but IMO does match


def test_un_eu():
    idx = make()
    r = lists.find(idx, ["Blue Wave Shipping Company owner and Ali Reza Karimi named", "Sinokor Merchant Marine Co fined"])
    assert {x["l"] for x in r} == {"UN", "EU"}


UK_NEW = b'Unique ID,Name,Name type,Designation type,Regime,Country\nRUS1,Blue Star Shipping Ltd,Primary Name,Entity,Russia,Panama\nRUS1,Azure Star Shipping,Alias,Entity,Russia,\nRUS2,Dmitri Alexeyevich Volkov,Primary Name,Individual,Russia,Russia\n'
UK_OLD = b'Last Updated,01/01/2026\nName 6,Name 1,Name 2,Name 3,Name 4,Name 5,Title,Group Type,Regime,Group ID,Country\nVOLKOV,Dmitri,Alexeyevich,,,,,Individual,Russia,7,Russia\nNORTH WIND TRADING,,,,,,,Entity,Russia,8,Cyprus\n'
CSL = b"source,entity_number,type,programs,name,alt_names,addresses\nEntity List (EL) - Bureau of Industry and Security,1,Entity,EAR,Zhongxing Test Instruments Co,ZTI Instruments,\"[{'address': 'x', 'country': 'CN'}]\"\nSpecially Designated Nationals (SDN) - Treasury Department,2,Entity,X,Dup Name Skipped Ltd,,\n"


def test_uk_and_us():
    idx = lists.Index()
    lists.parse_uk(UK_NEW, idx)
    lists.parse_uk(UK_OLD, idx)
    lists.parse_csl(CSL, idx, {"CN": "China"})
    names = {r[0] for r in idx.rows.values()}
    assert "Blue Star Shipping Ltd" in names and "Dmitri Alexeyevich Volkov" in names
    assert any(r[0].startswith("NORTH WIND") and r[4] == "Cyprus" for r in idx.rows.values())   # old OFSI format
    assert "Azure Star Shipping" not in names                      # alias is searchable but not a catalogue row
    assert lists.find(idx, ["Azure Star Shipping tanker"])          # ... and it still matches
    assert any(r[2] == "US EL" and r[4] == "China" for r in idx.rows.values())
    assert not any("Dup Name" in n for n in names)

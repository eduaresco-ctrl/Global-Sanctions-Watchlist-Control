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

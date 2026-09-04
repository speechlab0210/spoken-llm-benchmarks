"""Printed country names -> ISO 3166-1 alpha-2, and a light city normaliser. Shared by the geocoder and the builder."""
import re, unicodedata

_MAP = {
    "usa": "US", "u.s.a.": "US", "u.s.a": "US", "us": "US", "u.s.": "US", "united states": "US", "united states of america": "US", "america": "US",
    "uk": "GB", "u.k.": "GB", "united kingdom": "GB", "england": "GB", "scotland": "GB", "wales": "GB", "great britain": "GB", "northern ireland": "GB",
    "china": "CN", "p.r. china": "CN", "p. r. china": "CN", "pr china": "CN", "prc": "CN", "people's republic of china": "CN", "mainland china": "CN",
    "taiwan": "TW", "taiwan (r.o.c.)": "TW", "r.o.c.": "TW", "roc": "TW", "republic of china": "TW", "taiwan, roc": "TW",
    "hong kong": "HK", "hong kong sar": "HK", "hong kong, china": "HK", "hong kong sar, china": "HK", "hksar": "HK",
    "macau": "MO", "macao": "MO", "macau sar": "MO", "macao, china": "MO",
    "singapore": "SG", "japan": "JP", "korea": "KR", "south korea": "KR", "republic of korea": "KR", "korea, republic of": "KR",
    "germany": "DE", "france": "FR", "canada": "CA", "australia": "AU", "india": "IN", "italy": "IT", "spain": "ES", "the netherlands": "NL",
    "netherlands": "NL", "switzerland": "CH", "sweden": "SE", "israel": "IL", "united arab emirates": "AE", "uae": "AE", "poland": "PL",
    "czech republic": "CZ", "czechia": "CZ", "brazil": "BR", "finland": "FI", "norway": "NO", "denmark": "DK", "belgium": "BE", "austria": "AT",
    "portugal": "PT", "ireland": "IE", "greece": "GR", "turkey": "TR", "türkiye": "TR", "russia": "RU", "russian federation": "RU",
    "saudi arabia": "SA", "qatar": "QA", "vietnam": "VN", "viet nam": "VN", "thailand": "TH", "malaysia": "MY", "indonesia": "ID", "pakistan": "PK",
    "bangladesh": "BD", "mexico": "MX", "argentina": "AR", "chile": "CL", "south africa": "ZA", "egypt": "EG", "nigeria": "NG", "kenya": "KE",
    "rwanda": "RW", "uganda": "UG", "palestine": "PS", "romania": "RO", "hungary": "HU", "luxembourg": "LU", "new zealand": "NZ", "iran": "IR",
    "ukraine": "UA", "estonia": "EE", "latvia": "LV", "lithuania": "LT", "slovenia": "SI", "croatia": "HR", "serbia": "RS", "bulgaria": "BG",
    "slovakia": "SK", "iceland": "IS", "cyprus": "CY", "nepal": "NP", "sri lanka": "LK", "philippines": "PH", "colombia": "CO", "peru": "PE",
    "morocco": "MA", "tunisia": "TN", "kazakhstan": "KZ", "malta": "MT", "bahrain": "BH", "jordan": "JO", "lebanon": "LB", "kuwait": "KW", "oman": "OM",
    "ethiopia": "ET", "ghana": "GH", "tanzania": "TZ", "cameroon": "CM", "senegal": "SN", "algeria": "DZ", "mongolia": "MN", "uzbekistan": "UZ",
    "georgia": "GE", "armenia": "AM", "azerbaijan": "AZ", "belarus": "BY", "moldova": "MD", "north macedonia": "MK", "bosnia and herzegovina": "BA",
    "montenegro": "ME", "albania": "AL", "kosovo": "XK", "maldives": "MV", "iraq": "IQ", "syria": "SY", "yemen": "YE", "afghanistan": "AF", "bhutan": "BT",
    "cuba": "CU", "puerto rico": "PR", "north korea": "KP", "myanmar": "MM", "cambodia": "KH", "laos": "LA", "brunei": "BN", "fiji": "FJ",
}

def iso_of(name):
    """ISO alpha-2 for a printed country name; None when unknown or empty. Accepts a trailing period and case."""
    if not name: return None
    s = unicodedata.normalize("NFKC", str(name))
    s = re.sub(r"\(.*?\)", " ", s).split(";")[0]          # "Canada (Toronto group); USA (...)" -> "Canada"
    s = s.strip().strip(".").strip().lower()
    s = re.sub(r"\s+", " ", s)
    if s in _MAP: return _MAP[s]
    if len(s) == 2 and s.isalpha() and s.upper() in set(_MAP.values()): return s.upper()
    # "Beijing, China" style: last comma part
    if "," in s:
        return iso_of(s.split(",")[-1])
    return None

def norm_city(city):
    """First comma-separated part, trimmed; drops a trailing state/zip; keeps the printed spelling otherwise."""
    if not city: return None
    c = unicodedata.normalize("NFKC", str(city)).strip()
    c = c.split(",")[0].strip()
    c = re.sub(r"\s+\d{4,}$", "", c)          # zip codes
    c = re.sub(r"\s*\(.*?\)\s*$", "", c)      # trailing parentheses
    return c or None

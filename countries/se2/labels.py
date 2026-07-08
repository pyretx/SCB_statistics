"""SSYK-2012 group names + breakdown category labels for Sweden v2 (EN + SV).

Copied from the legacy page (scb_salaries.py) so SE2 needs no import of the
page script; when SE2 replaces the legacy page these become the single copy.
Group names are stored WITHOUT the "NN – " prefix (the framework's sidebar and
code browser prepend the code themselves).
"""
from __future__ import annotations

MAJOR_GROUPS = {
    "EN": {
        "0": "Armed forces",
        "1": "Managers",
        "2": "Professionals",
        "3": "Technicians & associate professionals",
        "4": "Clerical support workers",
        "5": "Service & sales workers",
        "6": "Agricultural, forestry & fishery",
        "7": "Craft & trades workers",
        "8": "Plant & machine operators",
        "9": "Elementary occupations",
    },
    "SV": {
        "0": "Militärt arbete",
        "1": "Chefer",
        "2": "Specialister",
        "3": "Tekniker & associate-specialister",
        "4": "Kontors- & kundservicearbete",
        "5": "Service-, omsorgs- & försäljningsarbete",
        "6": "Jordbruk, skogsbruk & fiske",
        "7": "Hantverksarbete",
        "8": "Process- & maskinoperatörsarbete",
        "9": "Arbete utan krav på särskild yrkesutbildning",
    },
}

SUB_GROUPS = {
    "EN": {
        "00": "Commissioned armed forces officers",
        "01": "Other armed forces occupations",
        "11": "Chief executives, senior officials & legislators",
        "12": "Administrative & commercial managers",
        "13": "Production & specialised services managers",
        "14": "Hospitality, retail & other services managers",
        "21": "Science & engineering professionals",
        "22": "Health professionals",
        "23": "Teaching professionals",
        "24": "Business & administration professionals",
        "25": "ICT professionals",
        "26": "Legal, social & cultural professionals",
        "31": "Science & engineering technicians",
        "32": "Health associate professionals",
        "33": "Business & administration associate professionals",
        "34": "Legal, social & cultural associate professionals",
        "35": "ICT technicians",
        "41": "General & keyboard clerks",
        "42": "Customer services clerks",
        "43": "Numerical & material recording clerks",
        "44": "Other clerical support workers",
        "51": "Personal service workers",
        "52": "Sales workers",
        "53": "Personal care workers",
        "54": "Protective services workers",
        "61": "Skilled agricultural workers",
        "62": "Skilled forestry, fishery & hunting workers",
        "71": "Building & related trades workers",
        "72": "Metal, machinery & related trades workers",
        "73": "Handicraft & printing workers",
        "74": "Electrical & electronics trades workers",
        "75": "Food, woodworking & other craft workers",
        "81": "Stationary plant & machine operators",
        "82": "Assemblers",
        "83": "Drivers & mobile plant operators",
        "91": "Cleaners & helpers",
        "92": "Agricultural & fishery labourers",
        "93": "Construction & manufacturing labourers",
        "94": "Food preparation assistants",
        "96": "Refuse workers & other elementary workers",
    },
    "SV": {
        "00": "Officerare",
        "01": "Övrig militär personal",
        "11": "Verkställande direktörer, högre ämbetsmän m.fl.",
        "12": "Administrativa chefer & kommersiella chefer",
        "13": "Produktionschefer & specialiserade servicechefer",
        "14": "Chefer inom hotell, handel & övrig serviceverksamhet",
        "21": "Naturvetare, matematiker & ingenjörer",
        "22": "Hälso- & sjukvårdsspecialister",
        "23": "Undervisningsspecialister",
        "24": "Affärs- & förvaltningsspecialister",
        "25": "IT-specialister",
        "26": "Jurister, samhällsvetare & kulturarbetare",
        "31": "Ingenjörer & tekniker",
        "32": "Hälso- & sjukvårdsassistenter",
        "33": "Affärs- & förvaltningsassistenter",
        "34": "Juridiska, sociala & kulturella assistenter",
        "35": "IT-tekniker",
        "41": "Kontorsassistenter m.fl.",
        "42": "Kundtjänstpersonal",
        "43": "Ekonomi- & lagerredovisare m.fl.",
        "44": "Övrig kontorspersonal",
        "51": "Servicearbetare",
        "52": "Försäljare",
        "53": "Omsorgsarbetare",
        "54": "Bevaknings- & säkerhetspersonal",
        "61": "Jordbrukare m.fl.",
        "62": "Skogsarbetare, fiskare & jägare",
        "71": "Byggnads- & anläggningsarbetare",
        "72": "Metallarbetare & verkstadsmekaniker",
        "73": "Hantverkare & grafiker",
        "74": "El- & elektronikmontörer",
        "75": "Livsmedels-, trä- & övriga hantverksarbetare",
        "81": "Maskin- & motoroperatörer",
        "82": "Montörer",
        "83": "Transport- & maskinförare",
        "91": "Städare m.fl.",
        "92": "Jord- & skogsbruksarbetare m.fl.",
        "93": "Bygg-, tillverknings- & transportarbetare",
        "94": "Köks- & restaurangbiträden",
        "96": "Återvinningsarbetare & övriga",
    },
}

# NUTS-2 régions (the region table's Region codes; "SE" total excluded from the
# breakdown chart — it is the national total, not a region).
REGIONS = {
    "EN": {
        "SE11": "Stockholm", "SE12": "East-Central Sweden",
        "SE21": "Småland & islands", "SE22": "South Sweden", "SE23": "West Sweden",
        "SE31": "North-Central Sweden", "SE32": "Central Norrland", "SE33": "Upper Norrland",
    },
    "SV": {
        "SE11": "Stockholm", "SE12": "Östra Mellansverige",
        "SE21": "Småland med öarna", "SE22": "Sydsverige", "SE23": "Västsverige",
        "SE31": "Norra Mellansverige", "SE32": "Mellersta Norrland", "SE33": "Övre Norrland",
    },
}

EDU_LEVELS = {
    "EN": {
        "1": "Primary ed. < 9 years", "2": "Primary ed. 9–10 years",
        "3": "Upper secondary ≤ 2 years", "4": "Upper secondary 3 years",
        "5": "Post-secondary < 3 years", "6": "Post-secondary ≥ 3 years",
        "7": "Post-graduate",
    },
    "SV": {
        "1": "Förgymnasial < 9 år", "2": "Förgymnasial 9–10 år",
        "3": "Gymnasial, högst 2 år", "4": "Gymnasial, 3 år",
        "5": "Eftergymnasial < 3 år", "6": "Eftergymnasial ≥ 3 år",
        "7": "Forskarutbildning",
    },
}

AGE_GROUPS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65-68"]

SECTORS = {
    "EN": {
        "0": "All sectors", "1-3": "Public sector (total)",
        "1": "Central government", "2": "Municipalities",
        "3": "County councils / Regions", "4-5": "Private sector (total)",
        "4": "Private sector – manual workers", "5": "Private sector – non-manual workers",
    },
    "SV": {
        "0": "Alla sektorer", "1-3": "Offentlig sektor (totalt)",
        "1": "Statlig sektor", "2": "Kommunal sektor",
        "3": "Regioner", "4-5": "Privat sektor (totalt)",
        "4": "Privat sektor – arbetare", "5": "Privat sektor – tjänstemän",
    },
}

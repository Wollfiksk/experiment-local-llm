"""
Experiment s lokálním LLM – asistent do kalendáře.

Model dostane českou větu ("Zítra v 15:00 trénink na hřišti") a má vrátit
událost jako JSON: {"nazev", "datum", "cas", "misto"}.

Skript projde všechny věty z testy.csv a pro každý model změří:
  - kolik odpovědí je platný JSON
  - přesnost jednotlivých polí (název, datum, čas, místo)
  - kolik událostí je celých správně (datum + čas + místo)
  - průměrný čas odpovědi
Výsledky uloží do vysledky.md (souhrn) a vysledky.csv (každá odpověď).

Spuštění:  python mereni.py
(server musí běžet: .\\ollama.exe serve)
"""

import csv
import json
import re
import sys
import time
import unicodedata
from datetime import datetime

import ollama

HOST = "http://localhost:11434"

# Prompt pro modely BEZ úprav – jen základní zadání, bez pravidel a příkladů.
ZAKLADNI_PROMPT = (
    "Dnes je úterý 24. 11. 2026. Z této věty vytáhni událost do kalendáře "
    'a vrať JSON {"nazev": ..., "datum": "RRRR-MM-DD", "cas": "HH:MM", '
    '"misto": ...}.\n\nVěta: '
)

# (název v tabulce, model v Ollamě, jestli přidat základní prompt)
KONFIGURACE = [
    ("qwen2.5:3b bez úprav", "qwen2.5:3b", True),
    ("llama3.2:3b bez úprav", "llama3.2:3b", True),
    ("kalendar-qwen (upravený)", "kalendar-qwen", False),
    ("kalendar-llama (upravený)", "kalendar-llama", False),
]

POLE = ["nazev", "datum", "cas", "misto"]

# trust_env=False: nepoužívat školní proxy, server běží na tomhle počítači
klient = ollama.Client(host=HOST, trust_env=False)


def normalizuj(text):
    """Malá písmena bez diakritiky – 'Hřiště' -> 'hriste'."""
    text = unicodedata.normalize("NFKD", str(text))
    return "".join(z for z in text if not unicodedata.combining(z)).lower().strip()


def prazdne(hodnota):
    return hodnota is None or normalizuj(hodnota) in ("", "null", "none", "-")


def uprav_datum(hodnota):
    """Převede datum na RRRR-MM-DD (zvládne i 25.11.2026)."""
    if prazdne(hodnota):
        return ""
    hodnota = str(hodnota).strip().replace(" ", "")
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(hodnota, fmt).date().isoformat()
        except ValueError:
            pass
    return hodnota


def uprav_cas(hodnota):
    """Převede čas na HH:MM ('8:00' -> '08:00')."""
    if prazdne(hodnota):
        return ""
    m = re.search(r"(\d{1,2})[:.](\d{2})", str(hodnota))
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else str(hodnota)


def obsahuje(hodnota, ocekavany_kus):
    """Prázdné očekávání = model má dát null. Jinak stačí, když text obsahuje kus slova."""
    if not ocekavany_kus:
        return prazdne(hodnota)
    return not prazdne(hodnota) and ocekavany_kus in normalizuj(hodnota)


def nacti_testy(soubor="testy.csv"):
    with open(soubor, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def zeptej_se(model, veta, pridat_prompt):
    obsah = (ZAKLADNI_PROMPT + veta) if pridat_prompt else veta
    odp = klient.chat(
        model=model,
        messages=[{"role": "user", "content": obsah}],
        format="json",  # Ollama donutí model psát JSON
    )
    return odp["message"]["content"]


def vyhodnot(odpoved, test):
    """Vrátí slovník pole -> True/False a jestli šel JSON přečíst."""
    try:
        data = json.loads(odpoved)
        if not isinstance(data, dict):
            raise ValueError
    except ValueError:
        return {p: False for p in POLE}, False, {}

    vysledek = {
        "nazev": obsahuje(data.get("nazev"), test["nazev_obsahuje"]),
        "datum": uprav_datum(data.get("datum")) == test["datum"],
        "cas": uprav_cas(data.get("cas")) == test["cas"],
        "misto": obsahuje(data.get("misto"), test["misto_obsahuje"]),
    }
    return vysledek, True, data


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # kvůli ✓ ✗ ve Windows konzoli
    testy = nacti_testy()
    print(f"Načteno {len(testy)} testovacích vět.\n")
    n = len(testy)
    detail, souhrn = [], []

    for nazev, model, pridat_prompt in KONFIGURACE:
        print(f"=== {nazev} ===")
        try:
            zeptej_se(model, "Zítra v 10:00 test.", pridat_prompt)  # zahřátí, neměří se
        except ollama.ResponseError as e:
            print(f"  Přeskakuji – model není dostupný ({e.error}).\n")
            continue

        body = {p: 0 for p in POLE}
        platny_json = cele_spravne = 0
        casy = []

        for i, test in enumerate(testy, 1):
            start = time.perf_counter()
            odpoved = zeptej_se(model, test["text"], pridat_prompt)
            cas = time.perf_counter() - start
            casy.append(cas)

            vysl, json_ok, data = vyhodnot(odpoved, test)
            platny_json += json_ok
            for p in POLE:
                body[p] += vysl[p]
            cele = vysl["datum"] and vysl["cas"] and vysl["misto"]
            cele_spravne += cele

            znacky = "".join("✓" if vysl[p] else "✗" for p in POLE)
            print(f"  {i:2}/{n} {znacky} {cas:5.2f} s  {test['text'][:35]:<35} -> "
                  f"{data.get('datum')} {data.get('cas')} {data.get('misto')}")
            detail.append([nazev, test["text"], odpoved.strip(), json_ok,
                           *(vysl[p] for p in POLE), cele, round(cas, 2)])

        souhrn.append({"nazev": nazev, "json": platny_json, "body": body,
                       "cele": cele_spravne, "cas": sum(casy) / n})
        print(f"  -> celé správně {cele_spravne}/{n}, průměrně {sum(casy) / n:.2f} s\n")

    if not souhrn:
        print("Žádný model neproběhl. Běží server a jsou modely stažené?")
        sys.exit(1)

    with open("vysledky.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["konfigurace", "veta", "odpoved", "platny_json",
                    *(f"{p}_ok" for p in POLE), "cele_spravne", "cas_s"])
        w.writerows(detail)

    def pct(x):
        return f"{100 * x / n:.0f} %"

    radky = ["# Výsledky měření", "", f"Počet testovacích vět: {n}", "",
             "| Konfigurace | Platný JSON | Název | Datum | Čas | Místo "
             "| **Celá událost** | Průměrný čas |",
             "|---|---|---|---|---|---|---|---|"]
    for s in souhrn:
        b = s["body"]
        radky.append(f"| {s['nazev']} | {pct(s['json'])} | {pct(b['nazev'])} "
                     f"| {pct(b['datum'])} | {pct(b['cas'])} | {pct(b['misto'])} "
                     f"| **{pct(s['cele'])}** ({s['cele']}/{n}) | {s['cas']:.2f} s |")
    radky += ["", "*Celá událost = správně datum, čas i místo zároveň.*", ""]

    with open("vysledky.md", "w", encoding="utf-8") as f:
        f.write("\n".join(radky))

    print("Hotovo. Souhrn je ve vysledky.md, detail ve vysledky.csv.")


if __name__ == "__main__":
    main()

# Experiment s lokálním LLM: asistent do kalendáře

## Úloha

Lidi si plánují věci ve zprávách běžnou řečí: *„zítra v 15:00 trénink na hřišti“*, *„kino v sobotu ve 20:30 v Cinestaru“*. Zkoumám, jestli malý jazykový model běžící **lokálně na školním PC** dokáže z takové české věty vytáhnout událost do kalendáře:

```json
{"nazev": "Trénink fotbalu", "datum": "2026-11-25", "cas": "15:00", "misto": "na hřišti"}
```

Takový asistent by se dal použít třeba v aplikaci na poznámky nebo v chatu. Všechno běží offline, takže soukromé zprávy nikam neodcházejí.

Co je na úloze těžké:
- **relativní data**: „zítra“, „v pátek“, „příští pondělí“, „za tři dny“
- **český způsob udávání času**: „v půl třetí“, „čtvrt na osm“, „ve 4 odpoledne“
- **věty bez času nebo bez místa**: „odevzdat projekt do pátku“

## Modely

| Model | Velikost | Výrobce |
|---|---|---|
| `qwen2.5:3b` | ~1,9 GB | Alibaba |
| `llama3.2:3b` | ~2,0 GB | Meta |

Oba se vejdou do limitu 4 GiB a mají podobnou velikost.

## Customizace

Oba modely jsem upravil stejným Modelfile (`Modelfile-qwen`, `Modelfile-llama`):

- **SYSTEM prompt**: popisuje roli a formát JSON a obsahuje **dnešní datum s tabulkou nejbližších dnů**. Model pak nemusí sám počítat, který den je „příští pondělí“.
- **Pravidla** pro převod českých časových výrazů („půl třetí“ = 14:30) a pro chybějící údaje (null).
- **Few-shot příklady** (`MESSAGE`): tři ukázkové věty se správným JSONem.
- **`temperature 0`**: stabilní a opakovatelné odpovědi.
- Ve skriptu navíc **`format="json"`**, takže Ollama nutí model odpovídat platným JSONem.

Pro srovnání měřím i **neupravené** modely, které dostanou jen dnešní datum a krátké zadání. Tak je vidět, co customizace přinesla.

## Postup

1. Rozbalit Ollamu na disk S: a spustit server: `.\ollama.exe serve`
2. Ve druhém okně stáhnout a upravit modely: `powershell -ExecutionPolicy Bypass -File .\priprav_modely.ps1`
3. Nainstalovat knihovnu: `pip install ollama`
4. Spustit měření: `python mereni.py`
5. Výsledky jsou ve `vysledky.md` (souhrn) a ve `vysledky.csv` (každá odpověď).
6. Smazat modely: `powershell -ExecutionPolicy Bypass -File .\smaz_modely.ps1`

## Měření

**Testovací data**: `testy.csv` obsahuje 30 vět se správnými odpověďmi. Datum v testech počítá s tím, že „dnes“ je úterý 24. 11. 2026.

Co se měří:
- **Platný JSON**: jestli šla odpověď vůbec přečíst.
- **Název**: jestli obsahuje klíčové slovo (např. „fotbal“).
- **Datum** a **čas**: musí přesně sedět.
- **Místo**: jestli obsahuje klíčové slovo, nebo je null, když ve větě žádné místo není.
- **Celá událost**: datum, čas i místo správně zároveň. Tohle je hlavní metrika.
- **Průměrný čas** odpovědi v sekundách. Model běží jen na procesoru a první načtení se nepočítá.

Testováno na: *(doplnit: procesor, RAM)*

## Výsledky a vyhodnocení

Tabulka výsledků je ve `vysledky.md`, každá odpověď ve `vysledky.csv`.
Vyhodnocení (který model se hodí, jestli by to šlo použít a co je potřeba splnit) je ve `vyhodnoceni.md`.

## Soubory

| Soubor | Obsah |
|---|---|
| `testy.csv` | testovací věty se správnými odpověďmi |
| `Modelfile-qwen`, `Modelfile-llama` | customizace modelů |
| `priprav_modely.ps1` | stáhne a vytvoří modely |
| `mereni.py` | měřicí skript |
| `smaz_modely.ps1` | smaže všechny modely |
| `vysledky.md`, `vysledky.csv` | výsledky měření |
| `vyhodnoceni.md` | vyhodnocení experimentu |

Modely nejsou součástí repozitáře a po experimentu byly smazány.

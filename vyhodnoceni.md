# Vyhodnocení experimentu: asistent do kalendáře

## Výsledky

| Konfigurace | Platný JSON | Název | Datum | Čas | Místo | **Celá událost** | Průměrný čas |
|---|---|---|---|---|---|---|---|
| qwen2.5:3b bez úprav | 100 % | 93 % | 63 % | 87 % | 70 % | **37 %** (11/30) | 2,24 s |
| llama3.2:3b bez úprav | 100 % | 87 % | 30 % | 80 % | 70 % | **20 %** (6/30) | 2,00 s |
| kalendar-qwen (upravený) | 100 % | 90 % | 70 % | 93 % | 93 % | **60 %** (18/30) | 2,28 s |
| kalendar-llama (upravený) | 100 % | 93 % | 70 % | 97 % | 100 % | **67 %** (20/30) | 1,93 s |

*Celá událost = správně datum, čas i místo zároveň.* Podrobné odpovědi jsou ve `vysledky.csv`.

## Vyhodnocení

### Který model se hodí víc

**Nejlépe dopadl upravený `kalendar-llama`**: 67 % celých událostí, 100 % míst, 97 % časů a zároveň byl nejrychlejší (1,93 s). Upravený Qwen byl těsně za ním (60 %).

Zajímavé je, že **bez úprav byl lepší Qwen** (37 % proti 20 %). Llama bez úprav často psala datum ve špatném tvaru (`12-12-2026`, `RRRR-12-06`) nebo úplně mimo (test ve čtvrtek dala na březen 2027). Po customizaci se ale zlepšila mnohem víc a Qwen předběhla. Rozdíl mezi upravenými modely je ovšem jen 2 věty z 30, takže při tak malém testu nejde říct, že je Llama jednoznačně lepší. Oba modely jsou na tom podobně.

### Pomohla customizace?

**Ano, výrazně.** Celá událost se zlepšila u Qwenu z 37 % na 60 % a u Llamy z 20 % na 67 %, tedy víc než trojnásobně.

- **Místo** (70 % → 93–100 %): neupravené modely si místo vymýšlely, když ve větě žádné nebylo („Neuvedeno“, „Nevíme“, „Online“, „škola“, a dokonce „Nepodálejte mi to, prosím!“). Pravidlo „když místo chybí, dej null“ spolu s příkladem to vyřešilo.
- **Datum**: tabulka nejbližších dnů v promptu pomohla hlavně u „zítra“, „pozítří“, „příští pondělí“ a u formátu RRRR-MM-DD.
- **Čas**: pomohla pravidla pro „ve 4 odpoledne“ a „do pátku“ (bez času).
- **Platný JSON** byl všude 100 %, to zajistil parametr `format="json"`.
- Na rychlost úpravy vliv neměly, všechno trvalo asi 2 s na větu.

### Kde modely chybovaly

1. **Dny v týdnu**, což je největší problém. U obou upravených modelů bylo 9 chybných dat a většinou šlo o posun o den. „V sobotu“ dal Qwen na pátek, „v neděli“ obě Llamy na sobotu a Qwen na pondělí. Upravený Qwen netrefil ani jednu ze 4 vět se sobotou nebo nedělí, přestože měl v promptu tabulku s přesnými daty. Malé modely se neumí spolehlivě „podívat do tabulky“.
2. **Rok u data bez roku**: „28. února“ dal Qwen na rok 2026 (do minulosti), „12. 12.“ na rok 2027, „Na Nový rok“ na 31. 12. a Llama dala Silvestr na 1. 1. 2027.
3. **České časy**: „čtvrt na osm“ (07:15) netrefil žádný model (08:40, 14:30, 04:08, 08:00), i když to bylo přímo v pravidlech. „Půl třetí“ zvládla jen upravená Llama.
4. **Sporné případy v testech**: u vět „Vrátit knížky do knihovny“ a „hovor přes Teams“ se dá diskutovat, jestli jde o místo. Qwen tam dal null, což není úplně špatně.

### Šlo by to použít?

**Jako automatické ukládání do kalendáře ne.** Třetina událostí by se uložila se špatným údajem, nejčastěji o den vedle, a to je u kalendáře horší, než kdyby se neuložilo nic.

**Jako návrh, který uživatel před uložením potvrdí, ano.** Model spolehlivě vytáhne název, čas a místo (93–100 %). Uživatel jen zkontroluje datum, což je pořád rychlejší než vyplňovat formulář. Výhodou je, že všechno běží offline na běžném PC bez grafické karty a soukromé zprávy nikam neodcházejí.

### Co by bylo potřeba splnit

- **Počítat datum v kódu, ne modelem.** Model by vracel jen to, co ve větě je (např. `"den": "sobota"`, `"posun_dni": 2`, `"cas_text": "čtvrt na osm"`), a skutečné datum a čas by spočítal Python. Počítání s kalendářem je přesně to, v čem malé modely selhávají a co kód zvládne vždy správně.
- **Doplňovat dnešní datum automaticky.** Teď je v Modelfile napevno 24. 11. 2026.
- **Kontrolovat výstup**: datum nesmí být v minulosti, čas musí být 00:00–23:59. Při chybě se zeptat uživatele.
- **Přesnost celé události aspoň kolem 90–95 %.** Teď je 67 %.
- **Rychlost**: 2 s na procesoru je pro jednu zprávu použitelné, pro hromadné zpracování by byl potřeba výkonnější počítač nebo grafická karta.
- **Víc testovacích dat**: 30 vět je málo na spolehlivé srovnání. Chybí opakované události („každé pondělí“), časové rozsahy („od 14 do 16“), překlepy a hovorová čeština.
- **Případně zkusit větší model** (např. `qwen2.5:7b`), který se ale do limitu 4 GiB nevejde.

### Závěr

Customizace pomocí Modelfile (pravidla, příklady, tabulka dní) měla větší vliv než volba modelu: zlepšila výsledek dvakrát až třikrát. Malé lokální modely do 4 GiB umí z české věty dobře vytáhnout *co* a *kde*, ale nejsou spolehlivé v tom, *kdy*. Prakticky použitelné řešení by kombinovalo model, který jen vytahuje údaje z textu, s klasickým kódem, který počítá data.

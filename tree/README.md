# Modulaire miniatuurbomen

Kale (dode/winter-)boom voor D&D-terrein, in twee printbare delen:

| Bestand | Omschrijving |
|---|---|
| `tree_bottom.stl` | Onderstel: ronde voet (⌀36 mm), wortels en schorsachtige stam met zaagsnede op 32 mm hoogte |
| `tree_crown.stl` | Losse kroon: 8 spreidende hoofdtakken met vertakte twijgen |
| `gen_tree.py` | Python-script (numpy, trimesh, manifold3d) waarmee beide STL's procedureel gegenereerd worden |
| `preview_*.png` | Previews van het gemonteerde geheel, onderstel en kroon |

**Geassembleerd:** ca. 96 mm hoog, voetafdruk ca. 48 × 42 mm. Geprint standaard FDM-laaghoogte is voldoende.

## Verbinding (pen + magneten)

- **Pen:** kroon heeft een geprinte pen ⌀4,0 × 6,5 mm; het onderstel heeft een bijpassende tule ⌀4,3 mm, 8 mm diep (0,15 mm speling per zijde).
- **Magneten:** 2 uitsparingen van **5,4 × 2,2 mm** in beide zaagvlakken — plaats er **5×2 mm-magneten** in (te lijmen, juiste poolrichting: de vlakken naar elkaar toe).

## Printinstructies

- **Onderstel:** print zoals gemodelleerd, voet plat op het printbed, geen supports nodig.
- **Kroon:** print **ondersteboven** (zaagvlak omhoog, pen als puntje op tafel). Gebruik supports "touching buildplate" voor de naar beneden wijzende takken. De magneetgaten komen zo open naar boven te liggen.
- Te strakke pen? Licht schuren of nalopen met een 4,2-4,3 mm boor. Te los? Een laagje lijk of verf op de pen.

## Aanpassen

Draai `python gen_tree.py` (vereist `pip install numpy trimesh manifold3d scipy`) en pas bovenin de parameters aan: `CROWN_H` (kroonhoogte), `BASE_R` (voet), `PIN_R`/`PIN_HOLE_R` (penpassing), `MAG_R`/`MAG_HOLE_R`/`MAG_DEPTH` (magneetmaat).

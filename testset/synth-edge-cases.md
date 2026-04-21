# Synthetisch edge-case document

Dit bestand test randgevallen die niet in de echte Leidse-regio documenten voorkomen maar wel door anonimizer afgehandeld moeten worden.

## Persoonsgegevens

Contactpersoon: Jan Pietersen.
BSN van de aanvrager: 111222333.
Rekeningnummer: NL91 ABNA 0417 1643 00.
Tweede rekening (geen spaties): NL39INGB0001234567.

## Mojibake-aas

Henri�tte Tans is een echte naam die door PDF-extractie als mojibake kan verschijnen. De tool moet hier waarschuwen maar niet crashen.

## Word-boundary-aas voor korte keys

Deze zinnen bevatten afkortingen die **niet** binnen andere woorden mogen worden vervangen:

- Het IB-beleid (niet: "het {IB}-beleid" vervangen binnen "biografie")
- De FG-portal (niet matchen binnen "overFGame")
- BIO-staging (niet matchen binnen "biography")

Maar deze moeten **wel** matchen als losse term:

- De IB&P is betrokken.
- BIO is de Baseline.

## Periode-notaties (geen telefoon)

- Periode 2021-2024 loopt nu.
- Versie 1.2.3.4 is uitgebracht.
- Hoofdstuk 14.2.7.1 beschrijft netwerkbeheer.

## Valide telefoon en email

Bel 070 373 80 11 of mail naar info@voorbeeld.nl.
Mobiel: +31 6 12345678.

## Adres-info

Bezoekadres: Turfmarkt 147, 2511 DP Den Haag.

## Interne organisatie-vermelding

Project IGNITE loopt bij Team Data & Analyse van cluster Ruimte.

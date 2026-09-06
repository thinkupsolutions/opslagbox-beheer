# Opslagbox Beheer v2

Online-ready prototype voor Windows en Android.

## Functies
- Beveiligde beheerder-login
- Klanten
- Boxen en tags
- Betalingen
- Zakelijke facturen
- Dashboard
- Centrale database-opzet
- Responsive webinterface voor Windows en Android
- Voorbereid voor latere Rabobank-integratie

## Starten

1. Installeer Python 3.11+
2. Open een terminal in deze map
3. Voer uit:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

4. Open:
http://127.0.0.1:8000

## Login en configuratie

Lokaal zijn de standaardgegevens `admin` / `wijzig-mij`. Stel online altijd
`ADMIN_USER`, `ADMIN_PASSWORD` en `SESSION_SECRET` in. De meegeleverde
`render.yaml` laat Render veilige waarden genereren of bij de eerste deployment
opvragen.

## Online zetten
Deze versie gebruikt lokaal SQLite en op Render een gekoppelde PostgreSQL-database.
Maak in Render een Blueprint aan vanuit de GitHub-repository; `render.yaml` maakt
de webservice en database samen aan.

## Rabobank
Er is bewust nog geen echte bankkoppeling ingebouwd. Hiervoor moeten later officiële
API-credentials en een veilige productieconfiguratie worden toegevoegd.

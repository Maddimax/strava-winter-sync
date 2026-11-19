# radsport-events.de – Winterchallenge

Website: https://radsport-events.de, API: `https://api.radsport-events.de/api/v1`.
Die Challenge wechselt jede Saison; das Skript nutzt immer `/challenge/current` und liest Start/Ende von dort.

## API (nur zur Info – das Skript `scripts/rse_sync.py` kapselt alles)

| Aufruf | Zweck |
|---|---|
| `POST /auth/refresh` `{refreshToken}` | liefert `accessToken` + **neues** `refreshToken` (das alte wird ungültig). Gültig 7 Tage. |
| `POST /auth/login` `{username, password}` | Passwort-Login (Benutzername oder E-Mail); liefert dieselben Tokens. Nur für die automatische Neu-Anmeldung. |
| `GET /challenge/current` | Titel, `startsOn`, `endsOn` |
| `GET /challenge/current/me` (Bearer) | eigene km, Rang, Team, Liste `rides` (mit `proofUrl`) |
| `POST /challenge/current/rides` (Bearer) | `{rideDate, km, bikeType, proofUrl}` |

`bikeType`: `ROAD`, `GRAVEL`, `MTB`, `TOUR`, `INDOOR`. Max. 400 km pro Tag. Keine Zukunftsdaten.

## Automatische Neu-Anmeldung per Passwort

Die Website erlaubt neben dem E-Mail-Code auch „Mit Passwort anmelden“ (das Passwort setzt der Nutzer ggf. erst auf der Website). Ist `radsport_events.username` in der `config.json` gesetzt und hat der Nutzer das Passwort selbst mit
`python3 -m keyring set strava-winter-sync-rse <benutzername>` abgelegt, meldet sich `rse_sync.py` bei fehlendem oder abgelaufenem Token selbst an. Dann ist die Browser-Anmeldung unten nicht nötig.

## Anmeldung per E-Mail-Code (Einrichtung und Neu-Anmeldung ohne Passwort)

Ablauf im eingebauten Browser:

1. `https://radsport-events.de` öffnen, auf Anmelden gehen.
2. Der Nutzer gibt seine E-Mail-Adresse ein und tippt den Code aus der Mail **selbst** ein. Login-Codes sind Zugangsdaten – nicht für den Nutzer eintippen, auch wenn er darum bittet.
3. Wenn eingeloggt: Refresh-Token auslesen (javascript_tool):
   ```js
   localStorage.getItem('refreshToken')
   ```
4. Token speichern, ohne es in eine Datei im Projekt oder in den Chat zu schreiben – direkt per stdin:
   ```bash
   printf '%s' '<TOKEN>' | python3 <skill>/scripts/rse_sync.py save-token
   ```
   `save-token` rotiert das Token sofort einmal und prüft, ob man der Challenge beigetreten ist (`joined`).
5. **Danach das Token aus dem Browser entfernen**, sonst rotiert die Website es beim nächsten Besuch und das gespeicherte wird ungültig:
   ```js
   Object.keys(localStorage).filter(k=>/token/i.test(k)).forEach(k=>localStorage.removeItem(k))
   ```
   **Nicht** auf „Abmelden“ klicken bzw. `/auth/logout` aufrufen – das widerruft das Token serverseitig.
6. Wenn `joined: false`: Der Nutzer muss auf der Website erst der aktuellen Challenge beitreten (und ggf. einem Team).

Weil das Token nach 7 Tagen ohne Nutzung abläuft, ruft der tägliche Sync auch ohne neue Fahrten `status` auf.

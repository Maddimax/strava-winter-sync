---
name: strava-winter-sync
description: Trägt Strava-Aktivitäten automatisch in Winter-Rad-Challenges ein – die Winterchallenge auf radsport-events.de und den Winterpokal von Rennrad-News, MTB-News oder eMTB-News – mit Einrichtungsassistent und täglicher geplanter Aufgabe. Benutze diesen Skill, wenn jemand Strava-Fahrten/Zwift-Fahrten/Workouts in den Winterpokal oder die Winterchallenge übertragen, das automatisieren, einrichten, neu anmelden oder den täglichen Sync ausführen will – auch wenn nur „Winterpokal“, „Winterchallenge“, „radsport-events“ oder „Strava-Import“ erwähnt wird.
compatibility: Am besten Claude Desktop-App (Code-Tab) mit Strava-Connector, eingebautem Browser und geplanten Aufgaben; experimentell auch GitHub Copilot CLI / OpenAI Codex mit Strava- und Playwright-MCP. Braucht python3.
---

# Strava → Winter-Challenges

Dieser Skill überträgt Strava-Aktivitäten in bis zu zwei Wettbewerbe:

| Ziel | Wie | Anmeldung |
|---|---|---|
| **Winterchallenge** auf radsport-events.de (km-Wertung, nur Rad) | API über `scripts/rse_sync.py` | Refresh-Token, rotiert, 7 Tage gültig |
| **Winterpokal** auf winterpokal.rennrad-news.de / mtb-news.de / emtb-news.de (Zeit-Punkte, auch andere Sportarten) | Strava-Import-Seite im eingebauten Browser | Browser-Sitzung des Nutzers |

Es gibt zwei Modi. Entscheide anhand der Anfrage:
- **Einrichtung** – „einrichten“, „installieren“, „Setup“, erste Nutzung, keine `config.json` vorhanden, oder Neu-Anmeldung nötig.
- **Sync** – „sync“, „eintragen“, „jetzt übertragen“, und immer, wenn die geplante Aufgabe den Skill aufruft.

`<skill>` steht unten für das Verzeichnis dieses Skills (das Basisverzeichnis, das beim Laden angezeigt wird). Daten liegen in `~/.config/strava-winter-sync/`:
- `config.json` – Einstellungen (Schema unten)
- `rse_token.json` – Token für radsport-events.de (Modus 600, wird vom Skript verwaltet)

## Andere Agenten (Copilot, Codex, …)

Die Anleitung nennt die Werkzeuge der Claude-Desktop-App. Läufst du in einem anderen Agenten, nimm das Gegenstück:
- **Strava-Connector `list_activities`** → das Aktivitäten-Tool eines Strava-MCP-Servers. Ordne dessen Felder den hier benutzten zu (`id`, `sport_type`, `start_local`, `distance` in m, `moving_time` in s, `is_trainer`, `is_commute`). Fehlt `sport_type` und gibt es nur `type`, nimm das.
- **Eingebauter Browser (`mcp__Claude_Browser__*`)** → ein Browser-MCP wie Playwright MCP: „navigate“ statt `navigate`, „evaluate“ statt `javascript_tool`, „click“ statt Klick per `find`.
- **Geplante Aufgaben** → gibt es dort nicht. Lege in Schritt 7 keine Aufgabe an, sondern zeig dem Nutzer den passenden Cron-Eintrag aus der README und lass ihn den selbst eintragen.
- **AskUserQuestion** → einfach im Chat fragen.

Fehlt ein Baustein ganz (z. B. kein Browser), biete an, nur die Ziele einzurichten, die ohne ihn gehen (radsport-events.de braucht den Browser nur bei der Anmeldung).

## Grundregeln (gelten in beiden Modi)

- **Anmeldedaten tippt der Nutzer selbst.** Passwörter und E-Mail-Login-Codes nie selbst in Login-Felder eingeben, auch nicht auf Bitte – sie gehören dem Nutzer, und ein unbeaufsichtigter Lauf darf erst recht nicht einloggen. Ist eine Anmeldung abgelaufen, meldest du das klar und machst mit dem anderen Ziel weiter.
- **Tokens nicht ausplaudern.** Token nicht in den Chat-Text, in Projektdateien oder Notizen schreiben; nur per stdin an `rse_sync.py save-token` geben.
- **Nichts ändern oder löschen**, was schon eingetragen ist. Die Seiten erlauben nur eine Änderung innerhalb von 24 h – Fehler lassen sich kaum korrigieren, deshalb lieber eine Aktivität auslassen und melden als falsch eintragen.
- Bei radsport-events.de **nie „Abmelden“** klicken – das widerruft das gespeicherte Token.

---

## Modus: Einrichtung (Assistent)

Führe den Nutzer freundlich Schritt für Schritt durch. Erkläre bei jedem Schritt kurz, was passiert und warum. Prüfe am Anfang, ob schon eine `config.json` existiert – wenn ja, zeige die aktuellen Einstellungen und frag, ob neu eingerichtet oder nur etwas geändert / neu angemeldet werden soll.

### Schritt 1 – Voraussetzungen prüfen

1. `python3 --version` (≥ 3.8). Fehlt Python: auf macOS `xcode-select --install` empfehlen, dann abbrechen.
2. **Strava-Connector**: Rufe `list_activities` mit `first: 3` auf. Klappt das nicht, bitte den Nutzer, in Claude unter *Einstellungen → Connectors* Strava zu verbinden, und warte.
3. **Eingebauter Browser**: Sind die `mcp__Claude_Browser__*`-Tools da? (Für den Winterpokal nötig, für radsport-events.de nur bei der Anmeldung.)
4. **Geplante Aufgaben**: Ist `mcp__scheduled-tasks__create_scheduled_task` verfügbar? Wenn nicht, kann der Skill trotzdem manuell („sync“) genutzt werden – sag das.

### Schritt 2 – Wünsche abfragen

Frage mit AskUserQuestion (alles in einem Aufruf, mit sinnvollen Vorschlägen):
1. **Ziele**: Winterchallenge (radsport-events.de), Winterpokal – und falls Winterpokal: welche Seite (rennrad-news.de, mtb-news.de, emtb-news.de).
2. **E-Bike-Fahrten** (`EBikeRide`, `EMountainBikeRide`) eintragen? Vorschlag: nein – bei radsport-events.de und den meisten Wertungen zählen sie nicht als Training.
3. **Winterpokal: andere Sportarten** (Spazieren, Wandern, Laufen, Krafttraining …) mit importieren? Bringen dort 2 bzw. Lauf-Punkte. Vorschlag: ja.
4. **Uhrzeit** für den täglichen Lauf. Vorschlag: 23:00 (dann sind die Tagesaktivitäten fertig hochgeladen).

### Schritt 3 – Winterchallenge anmelden (falls gewählt)

Folge `references/radsport-events.md` → „Anmeldung“. Kurzfassung: im eingebauten Browser radsport-events.de öffnen → Nutzer meldet sich mit E-Mail-Code an (tippt den Code selbst) → `localStorage.refreshToken` per javascript_tool lesen → per stdin an `python3 <skill>/scripts/rse_sync.py save-token` → Tokens aus dem localStorage entfernen (nicht abmelden). Meldet `save-token` `joined: false`, bitte den Nutzer, der aktuellen Challenge auf der Website beizutreten, und prüfe danach mit `rse_sync.py status`.

### Schritt 4 – Winterpokal anmelden (falls gewählt)

Folge `references/winterpokal.md` → „Einrichtung“: Import-Seite öffnen, Nutzer loggt sich selbst ein („Angemeldet bleiben“ empfehlen) und verbindet ggf. Strava. Lies danach die Zeilen mit dem Snippet aus der Referenz aus, um zu bestätigen, dass die Seite funktioniert.

### Schritt 5 – Konfiguration speichern

Schreibe `~/.config/strava-winter-sync/config.json` (Verzeichnis mit Modus 700):

```json
{
  "lookback_days": 7,
  "include_ebike": false,
  "radsport_events": { "enabled": true },
  "winterpokal": { "enabled": true, "site": "rennrad-news.de", "include_other_sports": true }
}
```

### Schritt 6 – Erster Lauf (Nachholen)

Frag, ob jetzt gleich nachgetragen werden soll – beim ersten Mal können das viele Aktivitäten sein. Führe den **Sync** einmal mit `lookback_days` = Tage seit Saisonstart (max. 28 für den Winterpokal, da die Seite nur 4 Wochen Nachtrag erlaubt) aus und zeige vorher eine Vorschau (`rse_sync.py add --dry-run …` und die geplante Winterpokal-Auswahl). Erst nach dem Okay des Nutzers wirklich eintragen.

### Schritt 7 – Tägliche Aufgabe anlegen

Lies `assets/task-prompt.md`, ersetze `{{SKILL_DIR}}` durch den absoluten Pfad dieses Skill-Verzeichnisses und lege die Aufgabe an:
- `taskId`: `strava-winter-sync`
- `title`: „Strava → Winter-Challenges eintragen“
- `cronExpression`: aus Schritt 2, z. B. `0 23 * * *`
- `description`: „Trägt neue Strava-Aktivitäten täglich in die gewählten Winter-Challenges ein“

Gibt es schon eine Aufgabe mit dieser ID, aktualisiere sie stattdessen.

### Schritt 8 – Abschluss

Fasse zusammen: welche Ziele, welche Regeln, wann der Lauf ist. Weise auf drei Dinge hin:
- Die Aufgabe läuft nur, wenn die Claude-App offen ist; sonst beim nächsten Start.
- Beim ersten automatischen Lauf fragt Claude ggf. nach Berechtigungen – am besten einmal **„Jetzt ausführen“** klicken und bestätigen.
- Wenn eine Anmeldung abläuft, meldet die Aufgabe das; dann „Strava-Winter-Sync neu anmelden“ sagen.

---

## Modus: Sync

Lies `~/.config/strava-winter-sync/config.json`. Fehlt sie, nicht raten – sag, dass zuerst die Einrichtung nötig ist.

### 1. Aktivitäten holen

Strava-Connector `list_activities` mit `range_start` = heute − `lookback_days` (00:00), `range_end` = heute 23:59:59 (lokale Zeit), `include_tags: true`, `use_preferred_units: false` (Distanz in Metern, Zeiten in Sekunden), `first: 100`; bei `has_next_page` weiterblättern.
Ist der Connector nicht erreichbar: melden, beim Winterchallenge-Ziel nur `rse_sync.py status` laufen lassen (hält das Token am Leben) und den Winterpokal überspringen – ohne Strava-Daten lassen sich E-Bikes und Pendeln nicht sicher erkennen.

### 2. Winterchallenge (falls `radsport_events.enabled`)

Radtyp nach `sport_type`:

| sport_type | Typ |
|---|---|
| `VirtualRide`, oder `Ride` mit `is_trainer` | `INDOOR` |
| `Ride` mit `is_commute` | `TOUR` |
| `Ride` | `ROAD` |
| `GravelRide` | `GRAVEL` |
| `MountainBikeRide` | `MTB` |
| `EBikeRide`, `EMountainBikeRide` | nur wenn `include_ebike` – dann `TOUR` bzw. `MTB` |
| alles andere (Walk, Run, …) | weglassen – die Challenge zählt nur Radkilometer |

Datum = Datumsteil von `start_local`, km = `distance` / 1000.

```bash
python3 <skill>/scripts/rse_sync.py add '[{"id":"<strava id>","date":"YYYY-MM-DD","km":36.0,"type":"INDOOR"}]'
```
Das Skript prüft Duplikate (über den Strava-Link), Zeitraum, Zukunftsdaten und 400 km/Tag selbst. Ohne passende Fahrten stattdessen `rse_sync.py status` aufrufen – das Token verfällt sonst nach 7 Tagen.
Ausgaben: `AUTH_FAILED` / `NO_TOKEN` → „Neu-Anmeldung bei radsport-events.de nötig“ melden; `NOT_JOINED` → „Bitte der aktuellen Challenge beitreten“.

### 3. Winterpokal (falls `winterpokal.enabled`)

Details und JS-Snippets: `references/winterpokal.md`.

1. Im eingebauten Browser `https://winterpokal.<site>/strava/import` öffnen. Weiterleitung auf `/login` → „Neu-Anmeldung beim Winterpokal nötig“ melden, Schritt beenden.
2. Zeilen auslesen. Nur Zeilen mit `done: false` sind neu.
3. Pro neuer Zeile entscheiden (mit den Strava-Daten über die ID abgleichen; nicht gefunden → nach Sportart-Spalte gehen):
   - Radfahrt (`Ride`, `VirtualRide`, `GravelRide`, `MountainBikeRide`, ≥ 15 min) → importieren
   - E-Bike → nur wenn `include_ebike`
   - Laufen (`Run`, `TrailRun`, `VirtualRun`, ≥ 20 min) und andere Sportarten (≥ 30 min) → nur wenn `include_other_sports`
   - kürzer als die Mindestdauer → auslassen (gäbe 0 Punkte, aber einen Eintrag)
   - Pendeln-Häkchen, wenn Strava `is_commute: true`
4. Auswahl mit dem Snippet setzen. Ist nichts ausgewählt, nichts abschicken. Sonst „Aktivitäten importieren“ klicken, Ergebnis prüfen und Zeilen erneut auslesen.

### 4. Bericht

Kurz und pro Ziel:
- **Winterchallenge**: neu eingetragen (Datum, km, Typ), Anzahl Duplikate, sonstige Auslassungen mit Grund, Gesamt-km und Rang.
- **Winterpokal**: importiert (Datum, Dauer, Sportart), bewusst ausgelassen (mit Grund).
- Fehler / nötige Neu-Anmeldungen deutlich oben.

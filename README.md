# strava-winter-sync

Ein [Claude](https://claude.ai)-Skill, der deine Strava-Aktivitäten jeden Tag automatisch in Winter-Rad-Challenges einträgt:

- **Winterchallenge** auf [radsport-events.de](https://radsport-events.de) (Kilometer-Wertung, nur Radfahrten)
- **Winterpokal** von [Rennrad-News](https://winterpokal.rennrad-news.de), [MTB-News](https://winterpokal.mtb-news.de) oder [eMTB-News](https://winterpokal.emtb-news.de) – über den Strava-Import der Seite, damit die Einträge auch im **Tracked-Ranking** zählen

Mit eingebautem Einrichtungsassistenten: Claude fragt dich, was du willst, führt dich durch die Anmeldungen, trägt die bisherige Saison nach (mit Vorschau) und legt eine tägliche Aufgabe an.

## Voraussetzungen

- **Claude-Desktop-App** (macOS/Windows) mit dem **Code-Tab** – nur dort gibt es den eingebauten Browser und geplante Aufgaben. Im reinen Web-Chat funktioniert es nicht.
- **Strava-Connector** in Claude verbunden (*Einstellungen → Connectors → Strava*)
- `python3` (auf dem Mac ggf. per `xcode-select --install`)
- Ein Konto bei radsport-events.de bzw. im Rennrad-News-/MTB-News-Forum, und du bist der jeweiligen Challenge beigetreten

## Installation

1. Unter [Releases](../../releases/latest) die Datei **`strava-winter-sync.skill`** herunterladen.
2. In Claude unter *Einstellungen → Fähigkeiten → Skills* hochladen.
3. Im Code-Tab schreiben: **„Richte den Strava-Winter-Sync ein“**.

Der Assistent erledigt den Rest. Passwörter und E-Mail-Codes tippst du dabei immer selbst ein – Claude gibt keine Zugangsdaten für dich ein.

## Was eingetragen wird

| Strava | Winterchallenge | Winterpokal |
|---|---|---|
| Ride, VirtualRide (Zwift), GravelRide, MountainBikeRide | ✅ (ROAD/INDOOR/GRAVEL/MTB, Pendeln → TOUR) | ✅ ab 15 min |
| E-Bike | optional | optional |
| Laufen | – | optional, ab 20 min |
| Spazieren, Wandern, Krafttraining, … | – | optional, ab 30 min („Alternative Sportarten“) |

Doppelte Einträge werden erkannt; bestehende Einträge werden nie geändert oder gelöscht.

## Gut zu wissen

- Die tägliche Aufgabe läuft nur, wenn die Claude-App offen ist (sonst beim nächsten Start).
- Klick nach der Einrichtung einmal auf **„Jetzt ausführen“** bei der Aufgabe und bestätige die Berechtigungen.
- **radsport-events.de:** Melde dich dort im normalen Browser nicht ab – das macht das gespeicherte Token ungültig. Läuft die Anmeldung ab, meldet die Aufgabe das; dann sag Claude „Strava-Winter-Sync neu anmelden“.
- Deine Daten (Einstellungen, Token) liegen nur lokal unter `~/.config/strava-winter-sync/`.

## Inhalt

```
SKILL.md                    Anleitung für Claude (Einrichtung + täglicher Sync)
scripts/rse_sync.py         radsport-events.de-API (Token-Rotation, Duplikat-Prüfung)
references/                 Details zu beiden Seiten
assets/task-prompt.md       Vorlage für die geplante Aufgabe
```

Kein offizielles Projekt von radsport-events.de, Rennrad-News, MTB-News oder Strava.

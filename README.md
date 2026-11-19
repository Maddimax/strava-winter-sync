# strava-winter-sync

Ein [Claude](https://claude.ai)-Skill, der deine Strava-Aktivitäten jeden Tag automatisch in Winter-Rad-Challenges einträgt:

- **Winterchallenge** auf [radsport-events.de](https://radsport-events.de) (Kilometer-Wertung, nur Radfahrten)
- **Winterpokal** von [Rennrad-News](https://winterpokal.rennrad-news.de), [MTB-News](https://winterpokal.mtb-news.de) oder [eMTB-News](https://winterpokal.emtb-news.de) – über den Strava-Import der Seite, damit die Einträge auch im **Tracked-Ranking** zählen

Mit eingebautem Einrichtungsassistenten: Claude fragt dich, was du willst, führt dich durch die Anmeldungen, trägt die bisherige Saison nach (mit Vorschau) und legt eine tägliche Aufgabe an.

## Voraussetzungen

- **Claude-Desktop-App** (macOS/Windows) mit dem **Code-Tab** – nur dort gibt es den eingebauten Browser und geplante Aufgaben. Im reinen Web-Chat funktioniert es nicht.
- **Strava-Connector** in Claude verbunden (*Einstellungen → Connectors → Strava*)
- Python 3.8+ (`python3` auf dem Mac, ggf. per `xcode-select --install`; `py` unter Windows, z. B. per `winget install Python.Python.3.12`)
- Ein Konto bei radsport-events.de bzw. im Rennrad-News-/MTB-News-Forum, und du bist der jeweiligen Challenge beigetreten
- Für den Winterpokal per Skript und die automatische Neu-Anmeldung: `python3 -m pip install --user keyring playwright` und `python3 -m playwright install chromium` (der Assistent hilft dabei)

Läuft auf macOS, Windows und Linux.

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
- **radsport-events.de:** Melde dich dort im normalen Browser nicht ab – das macht das gespeicherte Token ungültig. Läuft die Anmeldung ab, meldet die Aufgabe das; dann sag Claude „Strava-Winter-Sync neu anmelden“ – oder richte die automatische Neu-Anmeldung ein (unten).
- Deine Daten (Einstellungen, Token, Browser-Profil) liegen nur lokal unter `~/.config/strava-winter-sync/`.

## Automatische Neu-Anmeldung (optional)

Anmeldungen laufen irgendwann ab (radsport-events.de nach 7 Tagen ohne Lauf, Winterpokal nach Ablauf der Forum-Sitzung). Damit du dich dann nicht selbst neu anmelden musst, kannst du deine Passwörter im Passwort-Speicher deines Systems hinterlegen – unter macOS im Schlüsselbund, unter Windows in der Anmeldeinformationsverwaltung, unter Linux im Secret Service. Die Skripte lesen sie nur, wenn eine Anmeldung abgelaufen ist; Claude sieht sie nie.

```bash
python3 -m pip install --user keyring
python3 -m keyring set strava-winter-sync-rse DEIN_BENUTZERNAME
python3 -m keyring set strava-winter-sync-winterpokal DEIN_BENUTZERNAME
```

(Unter Windows `py` statt `python3`.) Der Befehl fragt verdeckt nach dem Passwort. Den Benutzernamen trägt der Assistent in die `config.json` ein. Bei radsport-events.de brauchst du dafür ein Passwort – falls du dich bisher nur per E-Mail-Code anmeldest, setz zuerst eines auf der Website. Eine Zwei-Faktor-Anmeldung im Forum wird nicht unterstützt.

## Mit GitHub Copilot oder OpenAI Codex (experimentell, ungetestet)

Der Skill folgt dem offenen [Agent-Skills](https://agentskills.io)-Format (`SKILL.md`), das auch die **GitHub Copilot CLI** und **OpenAI Codex** verstehen. Am bequemsten ist er aber mit Claude, weil er drei Bausteine der Claude-App nutzt. In anderen Agenten musst du diese selbst ersetzen:

| Claude-App | Ersatz bei Copilot / Codex |
|---|---|
| Strava-Connector | ein Strava-MCP-Server (es gibt mehrere Community-Projekte). Der Skill erwartet pro Aktivität `id`, `sport_type`, `start_local`, `distance` (m), `moving_time`, `is_trainer`, `is_commute` – je nach Server muss der Agent die Felder zuordnen. |
| Eingebauter Browser | Mit `winterpokal_sync.py` und der automatischen Neu-Anmeldung gar nicht nötig. Sonst [Playwright MCP](https://github.com/microsoft/playwright-mcp) mit dauerhaftem Browser-Profil. |
| Geplante Aufgaben | `cron` (Linux/macOS) bzw. `launchd` oder Aufgabenplanung (Windows), die den Agenten nicht-interaktiv startet (siehe unten). |

Beide Skripte brauchen nur Python (plus `keyring`/`playwright`) und funktionieren überall gleich.

### Installation

Den Ordner dieses Repos als `strava-winter-sync` in das Skill-Verzeichnis kopieren:

```bash
# GitHub Copilot CLI
git clone https://github.com/Maddimax/strava-winter-sync ~/.copilot/skills/strava-winter-sync

# OpenAI Codex
git clone https://github.com/Maddimax/strava-winter-sync ~/.codex/skills/strava-winter-sync
```

Danach den Agenten neu starten (in der Copilot CLI reicht `/skills reload`) und die MCP-Server für Strava und Playwright in dessen Konfiguration eintragen.

Dann wie bei Claude: **„Richte den Strava-Winter-Sync ein“**. Den Schritt „Tägliche Aufgabe anlegen“ kann der Assistent dort nicht selbst erledigen – lege stattdessen einen Cron-Job an, z. B. täglich um 23:00:

```cron
# Copilot CLI
0 23 * * * copilot -p "Führe den Skill strava-winter-sync im Modus Sync aus." --allow-all-tools >> ~/.config/strava-winter-sync/sync.log 2>&1
# Codex
0 23 * * * codex exec "Führe den Skill strava-winter-sync im Modus Sync aus." >> ~/.config/strava-winter-sync/sync.log 2>&1
```

Unter Windows statt Cron die Aufgabenplanung, z. B.:

```powershell
schtasks /Create /SC DAILY /ST 23:00 /TN strava-winter-sync /TR "copilot -p \"Führe den Skill strava-winter-sync im Modus Sync aus.\" --allow-all-tools"
```

Prüf vorher, welche Berechtigungs-Optionen deine Version für unbeaufsichtigte Läufe braucht, und gib nur so viele Rechte wie nötig. Rückmeldungen, ob und wie es bei dir läuft, gern als Issue.

## Inhalt

```
SKILL.md                    Anleitung für Claude (Einrichtung + täglicher Sync)
scripts/rse_sync.py         radsport-events.de-API (Token-Rotation, Duplikat-Prüfung, Passwort-Login)
scripts/winterpokal_sync.py Winterpokal-Strava-Import per Playwright (inkl. Forum-Login)
scripts/credentials.py      Passwörter aus dem System-Passwort-Speicher (keyring)
references/                 Details zu beiden Seiten
assets/task-prompt.md       Vorlage für die geplante Aufgabe
```

Kein offizielles Projekt von radsport-events.de, Rennrad-News, MTB-News oder Strava.

## Lizenz

[MIT](LICENSE)

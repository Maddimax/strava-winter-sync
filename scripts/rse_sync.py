#!/usr/bin/env python3
"""Strava-Fahrten in die Winterchallenge auf radsport-events.de eintragen.

Aufruf:
  rse_sync.py save-token            # Refresh-Token von stdin lesen und speichern (Einrichtung)
  rse_sync.py status                # Stand abfragen (erneuert dabei das Token)
  rse_sync.py add '<json>'          # [{"id": "<strava id>", "date": "YYYY-MM-DD", "km": 12.3, "type": "INDOOR"}]
  rse_sync.py add --dry-run '<json>'

Typen: ROAD, GRAVEL, MTB, TOUR, INDOOR. Duplikate werden über den Strava-Link (proofUrl) erkannt.
Daten liegen in $STRAVA_WINTER_SYNC_DIR (Standard: ~/.config/strava-winter-sync).
Das Refresh-Token wird bei jedem Lauf rotiert und ist 7 Tage gültig.

Automatische Neu-Anmeldung (optional, macOS/Windows/Linux): Steht in config.json
radsport_events.username und liegt im Passwort-Speicher des Systems ein Eintrag
"strava-winter-sync-rse" für diesen Benutzer (siehe credentials.py / README), meldet sich
das Skript damit selbst an, wenn das Token fehlt oder abgelaufen ist.

Exit-Meldungen, auf die der Aufrufer reagieren soll:
  NO_TOKEN      – noch keine Einrichtung (und kein Schlüsselbund-Eintrag)
  AUTH_FAILED   – Token abgelaufen/ungültig und kein (funktionierender) Passwort-Login → neu anmelden
  NOT_JOINED    – Benutzer ist der aktuellen Challenge nicht beigetreten
"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

from credentials import get_password

if hasattr(sys.stdout, "reconfigure"):  # Windows-Konsole: Umlaute/JSON sicher ausgeben
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

API = "https://api.radsport-events.de/api/v1"
DIR = os.path.expanduser(os.environ.get("STRAVA_WINTER_SYNC_DIR", "~/.config/strava-winter-sync"))
TOKEN = os.path.join(DIR, "rse_token.json")
CONFIG = os.path.join(DIR, "config.json")
TYPES = {"ROAD", "GRAVEL", "MTB", "TOUR", "INDOOR"}
MAX_KM_PER_DAY = 400
KEYCHAIN_SERVICE = "strava-winter-sync-rse"


def call(method, path, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(API + path, method=method, headers=headers,
                                 data=None if body is None else json.dumps(body).encode())
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw


def write_token(rt):
    os.makedirs(DIR, mode=0o700, exist_ok=True)
    tmp = TOKEN + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"refreshToken": rt}, f)
    os.chmod(tmp, 0o600)
    os.replace(tmp, TOKEN)


def stored_login():
    """(Benutzername, Passwort) für die automatische Anmeldung, sonst None.
    Benutzername: config.json → radsport_events.username; Passwort: Passwort-Speicher des Systems."""
    try:
        with open(CONFIG) as f:
            user = json.load(f).get("radsport_events", {}).get("username")
    except (OSError, ValueError):
        return None
    pw = get_password(KEYCHAIN_SERVICE, user)
    return (user, pw) if pw else None


def password_login(reason):
    creds = stored_login()
    if not creds:
        return None
    st, data = call("POST", "/auth/login", {"username": creds[0], "password": creds[1]})
    if st != 200 or not isinstance(data, dict) or "accessToken" not in data:
        sys.exit(f"AUTH_FAILED: {reason}; Passwort-Login lieferte {st}: {str(data)[:120]}")
    print(f"INFO: {reason} – mit Passwort aus dem Schlüsselbund neu angemeldet.", file=sys.stderr)
    return data


def access_token():
    if not os.path.exists(TOKEN):
        data = password_login("kein Token")
        if not data:
            sys.exit(f"NO_TOKEN: {TOKEN} fehlt – Einrichtung nötig.")
    else:
        with open(TOKEN) as f:
            rt = json.load(f)["refreshToken"]
        st, data = call("POST", "/auth/refresh", {"refreshToken": rt})
        if st != 200 or not isinstance(data, dict) or "accessToken" not in data:
            data = password_login(f"Token abgelaufen (refresh {st})")
            if not data:
                sys.exit(f"AUTH_FAILED: refresh lieferte {st}. Neu-Anmeldung bei radsport-events.de nötig.")
    write_token(data["refreshToken"])
    return data["accessToken"]


def save_token():
    rt = sys.stdin.read().strip().strip('"')
    if len(rt) < 20:
        sys.exit("Kein gültiges Token auf stdin.")
    write_token(rt)
    try:
        at = access_token()  # sofort einmal rotieren = prüfen, ob es funktioniert
    except SystemExit:
        os.remove(TOKEN)  # kein ungültiges Token liegen lassen
        raise
    st, me = call("GET", "/challenge/current/me", token=at)
    print(json.dumps({"saved": True, "joined": st == 200 and bool(me)}))


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if args[0] == "save-token":
        return save_token()
    at = access_token()
    _, summary = call("GET", "/challenge/current")
    st, me = call("GET", "/challenge/current/me", token=at)
    if st != 200 or not me:
        sys.exit(f"NOT_JOINED: /challenge/current/me lieferte {st}. Bitte auf radsport-events.de der Challenge beitreten.")
    if args[0] == "status":
        print(json.dumps({"challenge": summary.get("title"), "startsOn": summary.get("startsOn"),
                          "endsOn": summary.get("endsOn"), "km": me["km"], "rank": me["rank"],
                          "rides": len(me["rides"]), "team": (me.get("team") or {}).get("name")},
                         ensure_ascii=False))
        return
    if args[0] != "add":
        sys.exit(__doc__)

    dry = "--dry-run" in args
    items = json.loads([a for a in args[1:] if a != "--dry-run"][0])
    today = datetime.date.today().isoformat()
    have = {r.get("proofUrl") for r in me["rides"]}
    per_day = {}
    for r in me["rides"]:
        per_day[r["rideDate"]] = per_day.get(r["rideDate"], 0) + float(r["km"])

    added, skipped = [], []
    for it in sorted(items, key=lambda x: x["date"]):
        url = f"https://www.strava.com/activities/{it['id']}"
        km = round(float(it["km"]), 1)
        d, t = it["date"], it["type"]
        why = None
        if url in have:
            why = "schon eingetragen"
        elif t not in TYPES:
            why = f"unbekannter Typ {t}"
        elif d < summary["startsOn"] or d > summary["endsOn"]:
            why = "außerhalb der Challenge"
        elif d > today:
            why = "Zukunft"
        elif km < 1:
            why = "unter 1 km"
        elif per_day.get(d, 0) + km > MAX_KM_PER_DAY:
            why = "über 400 km/Tag"
        if why:
            skipped.append({"id": it["id"], "date": d, "km": km, "grund": why})
            continue
        if not dry:
            st, res = call("POST", "/challenge/current/rides",
                           {"rideDate": d, "km": km, "bikeType": t, "proofUrl": url}, token=at)
            if st not in (200, 201):
                skipped.append({"id": it["id"], "date": d, "km": km, "grund": f"API {st}: {str(res)[:120]}"})
                continue
        per_day[d] = per_day.get(d, 0) + km
        have.add(url)
        added.append({"id": it["id"], "date": d, "km": km, "type": t})

    if not dry:
        _, me = call("GET", "/challenge/current/me", token=at)
    print(json.dumps({"dry_run": dry, "added": added, "skipped": skipped,
                      "total_km": me["km"], "rank": me["rank"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

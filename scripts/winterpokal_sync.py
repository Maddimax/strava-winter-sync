#!/usr/bin/env python3
"""Strava-Aktivitäten über die Strava-Import-Seite in den Winterpokal importieren
(Rennrad-News / MTB-News / eMTB-News) – ohne Claude-Browser, per Playwright.

Aufruf:
  winterpokal_sync.py [--dry-run] [--commute ID,ID,...] [--headed]

Einstellungen aus $STRAVA_WINTER_SYNC_DIR/config.json (Standard: ~/.config/strava-winter-sync):
  winterpokal.site                 rennrad-news.de | mtb-news.de | emtb-news.de
  winterpokal.include_other_sports Laufen/Spazieren/… mit importieren (Standard: true)
  include_ebike                    E-Bike-Fahrten importieren (Standard: false)

Regeln (wie im Skill): schon importierte Zeilen bleiben unberührt; Radfahrten ab 15 min,
Laufen ab 20 min, andere Sportarten ab 30 min; kürzere Aktivitäten werden nicht importiert
(sie gäben 0 Punkte); „Ignorieren“ wird nie angekreuzt; Pendeln für die IDs aus --commute.

Anmeldung: Die Browser-Sitzung liegt in $STRAVA_WINTER_SYNC_DIR/winterpokal-profile.
Ist sie abgelaufen, steht winterpokal.username in config.json und liegt im Passwort-Speicher
des Systems ein Eintrag "strava-winter-sync-winterpokal" für diesen Benutzer (siehe
credentials.py / README), meldet sich das Skript damit im Forum an.

Ausgabe: eine JSON-Zeile. Exit-Codes: 0 ok, 1 Einrichtung fehlt, 2 AUTH_FAILED, 3 Import unbestätigt.
Benötigt: python3 -m pip install --user playwright keyring && python3 -m playwright install chromium
(unter Windows „py“ statt „python3“).
"""
import json
import os
import re
import sys

from credentials import get_password

if hasattr(sys.stdout, "reconfigure"):  # Windows-Konsole: Umlaute/JSON sicher ausgeben
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

DIR = os.path.expanduser(os.environ.get("STRAVA_WINTER_SYNC_DIR", "~/.config/strava-winter-sync"))
CONFIG = os.path.join(DIR, "config.json")
PROFILE = os.path.join(DIR, "winterpokal-profile")
KEYCHAIN_SERVICE = "strava-winter-sync-winterpokal"
RIDES = {"Ride", "VirtualRide", "GravelRide", "MountainBikeRide"}
EBIKES = {"EBikeRide", "EMountainBikeRide"}
RUNS = {"Run", "TrailRun", "VirtualRun"}


def logged_out(page):
    return "/login" in page.url or "Du musst eingeloggt sein" in page.content()


def login(page, base, import_url, user):
    pw = get_password(KEYCHAIN_SERVICE, user)
    if not pw:
        return ("Sitzung abgelaufen; keine automatische Anmeldung eingerichtet "
                f"(winterpokal.username in config.json + Passwort-Speicher-Eintrag '{KEYCHAIN_SERVICE}')")
    creds = (user, pw)
    page.goto(base + "/login", wait_until="domcontentloaded")
    link = page.locator('a[href*="/forum/login"]')
    if not link.count():
        return "Forum-Login-Link nicht gefunden"
    page.goto(link.first.get_attribute("href"), wait_until="domcontentloaded")
    form = page.locator('form[action$="/login/login"]').filter(has=page.locator('input[name="password"]'))
    form.locator('input[name="login"]').fill(creds[0])
    form.locator('input[name="password"]').fill(creds[1])
    form.locator('button[type="submit"]').first.click()
    page.wait_for_load_state("domcontentloaded")
    if page.locator('form[action$="/login/login"] input[name="password"]').count():
        return "Forum-Login abgelehnt (Passwort falsch?)"
    page.goto(base + "/login", wait_until="domcontentloaded")
    if logged_out(page) and page.locator('a[href*="/forum/login"]').count():
        page.locator('a[href*="/forum/login"]').first.click()
        page.wait_for_load_state("domcontentloaded")
    page.goto(import_url, wait_until="domcontentloaded")
    return "nach dem Forum-Login immer noch abgemeldet (Zwei-Faktor?)" if logged_out(page) else None


def decide(sport, mins, cfg):
    if sport in EBIKES:
        return None if cfg.get("include_ebike") else "E-Bike"
    if sport in RIDES:
        return None if mins >= 15 else "unter 15 min"
    if not cfg["winterpokal"].get("include_other_sports", True):
        return "andere Sportart"
    if sport in RUNS:
        return None if mins >= 20 else "unter 20 min"
    return None if mins >= 30 else "unter 30 min"


def main():
    args = sys.argv[1:]
    if args and args[0] in ("-h", "--help"):
        sys.exit(__doc__)
    try:
        with open(CONFIG) as f:
            cfg = json.load(f)
        site = cfg["winterpokal"]["site"]
    except (OSError, ValueError, KeyError):
        print(json.dumps({"error": f"NO_CONFIG: {CONFIG} fehlt oder ohne winterpokal.site – Einrichtung nötig."}))
        sys.exit(1)
    dry = "--dry-run" in args
    commute = set()
    if "--commute" in args:
        commute = {x.strip() for x in args[args.index("--commute") + 1].split(",") if x.strip()}
    base = f"https://winterpokal.{site}"
    import_url = base + "/strava/import"

    from playwright.sync_api import sync_playwright
    out = {"dry_run": dry, "relogin": False, "imported": [], "skipped": [], "already": 0}
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(PROFILE, headless="--headed" not in args, locale="de-DE")
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.goto(import_url, wait_until="domcontentloaded")
            if logged_out(page):
                out["relogin"] = True
                err = login(page, base, import_url, cfg["winterpokal"].get("username"))
                if err:
                    out["error"] = "AUTH_FAILED: " + err
                    print(json.dumps(out, ensure_ascii=False))
                    sys.exit(2)
            form = page.locator('form[action$="create_entries"]')
            boxes = form.locator('input[type=checkbox][name$="[import]"]')
            chosen = []
            for i in range(boxes.count()):
                cb = boxes.nth(i)
                sid = re.search(r"strava\[(\d+)\]", cb.get_attribute("name")).group(1)
                if cb.is_disabled():
                    out["already"] += 1
                    continue
                row = cb.locator("xpath=ancestor::tr[1]")
                date = row.locator("td.date").inner_text().strip()
                mins = int(re.sub(r"\D", "", row.locator("td.duration").inner_text()) or 0)
                sport = row.locator("td.category").inner_text().strip().split()[0]
                name = row.locator("span.notes").inner_text().strip() if row.locator("span.notes").count() else ""
                info = {"id": sid, "date": date, "min": mins, "sport": sport, "name": name}
                why = decide(sport, mins, cfg)
                if why:
                    cb.uncheck()
                    out["skipped"].append({**info, "grund": why})
                    continue
                cb.check()
                cm = form.locator(f'input[name="strava[{sid}][commute]"]')
                if cm.count() and not cm.is_disabled():
                    cm.set_checked(sid in commute)
                chosen.append({**info, "commute": sid in commute})
            if chosen and not dry:
                form.locator("button[type=submit]").first.click()
                page.wait_for_load_state("domcontentloaded")
                if "wurden importiert" not in page.inner_text("body"):
                    out["error"] = "IMPORT_UNCONFIRMED: keine Erfolgsmeldung, Seite " + page.url
                    out["imported"] = chosen
                    print(json.dumps(out, ensure_ascii=False))
                    sys.exit(3)
            out["imported"] = chosen
        finally:
            ctx.close()
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()

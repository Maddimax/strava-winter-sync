# Winterpokal (Rennrad-News / MTB-News / eMTB-News)

Drei Seiten mit derselben Software – nur die Domain unterscheidet sich:
- `https://winterpokal.rennrad-news.de`
- `https://winterpokal.mtb-news.de`
- `https://winterpokal.emtb-news.de`

Saison: 1. November bis Ende März. Einträge können bis 28 Tage nachgetragen werden.

## Punkte (Stand Saison 2026/27)

| Kategorie | Punkte | Mindestdauer, damit es zählt |
|---|---|---|
| Radfahren (auch Rolle/Zwift), Skilanglauf | 1 pro 15 min | 15 min |
| Laufen | 1 pro 20 min | 20 min |
| Alternative Sportarten (Studio, Wandern, Spazieren, Schwimmen, …) | pauschal 2 | 30 min |

Stretching zählt nicht.

## Warum über die Strava-Import-Seite (und nicht die API)

Es gibt eine offizielle API (Header `api-token`, `POST /api/v1/entries/add.json`). Über sie eingetragene Einträge zählen aber **nicht** im „Tracked“-Ranking – nur importierte Aktivitäten tun das. Deshalb nutzt dieser Skill die Import-Seite mit der gespeicherten Anmeldung des Nutzers – entweder per `scripts/winterpokal_sync.py` (Playwright, eigenes Browser-Profil) oder im eingebauten Browser. Der Strava-Import läuft **nicht** automatisch; man muss ihn auf der Seite auslösen.

## Anmeldung (Forum-Login)

Die Winterpokal-Seiten nutzen das Forum-Konto (XenForo). `…/login` verlinkt auf `https://www.<domain>/forum/login/?_xfRedirect=winterpokal`. Das Formular (`action` `/forum/login/login`) hat die Felder `login` (Benutzername oder E-Mail) und `password` in einem Schritt, „Angemeldet bleiben“ ist vorausgewählt (`remember=1`), kein Captcha. Danach gelangt man per Single-Sign-on zurück zum Winterpokal. Eine im Forum aktivierte Zwei-Faktor-Anmeldung kann das Skript nicht erledigen.

`winterpokal_sync.py` meldet sich dort nur an, wenn die Sitzung im Skript-Profil abgelaufen ist, `winterpokal.username` gesetzt ist und das Passwort im Passwort-Speicher liegt (`python3 -m keyring set strava-winter-sync-winterpokal <benutzername>`).

## Einrichtung

1. Im eingebauten Browser `https://winterpokal.<domain>/strava/import` öffnen.
2. Landet man auf `/login` („Du musst eingeloggt sein“): über den Link „Anmelden“ zum Forum-Login. Der Nutzer loggt sich **selbst** ein (Passwort tippt er selbst). Am besten „Angemeldet bleiben“ ankreuzen, damit die Sitzung lange hält.
3. Ist Strava noch nicht verbunden, zeigt die Seite einen Button zum Verbinden. Die Strava-Freigabe (OAuth) bestätigt der Nutzer selbst.
4. Fertig, wenn die Seite eine Tabelle mit Strava-Aktivitäten (oder „keine Aktivitäten“) zeigt.

## Import-Seite – Aufbau

Formular mit `action` `…/strava/create_entries` (POST, mit `csrf_token`). Pro Aktivität eine Tabellenzeile:

- `input.import` name=`strava[<StravaID>][import]` – importieren
- name=`strava[<StravaID>][commute]` – Pendeln
- name=`strava[<StravaID>][ignore]` – „beim nächsten Mal nicht vorauswählen“ (nicht benutzen)
- Zeile mit Klasse `importDisabled` / deaktivierte Checkbox = **schon importiert**
- Spalten: Datum (`td.date`, „13.11.“), Dauer (`td.duration`, „61 min“), Sportart (`td.category`, Strava-`sport_type` + Name in `span.notes`)

Zeilen auslesen (javascript_tool):
```js
(() => {
  const f = document.querySelector('form[action$="create_entries"]');
  if (!f) return {form: false, url: location.href, text: document.body.innerText.slice(0, 300)};
  return [...f.querySelectorAll('tr')].slice(1).map(r => {
    const cb = r.querySelector('input.import');
    return {
      id: cb?.name.match(/\[(\d+)\]/)?.[1],
      done: r.classList.contains('importDisabled') || !!cb?.disabled,
      checked: !!cb?.checked,
      date: r.querySelector('td.date')?.innerText.trim(),
      minutes: parseInt(r.querySelector('td.duration')?.innerText) || 0,
      sport: r.querySelector('td.category')?.childNodes[0]?.textContent.trim(),
      name: r.querySelector('span.notes')?.innerText.trim()
    };
  });
})()
```

Auswahl setzen (nur in diesem Formular; `want` = Liste der zu importierenden IDs, `commute` = IDs mit Pendeln):
```js
((want, commute) => {
  const f = document.querySelector('form[action$="create_entries"]');
  for (const cb of f.querySelectorAll('input.import:not([disabled])')) {
    const id = cb.name.match(/\[(\d+)\]/)[1];
    cb.checked = want.includes(id);
    const c = f.querySelector(`input[name="strava[${id}][commute]"]`);
    if (c && !c.disabled) c.checked = commute.includes(id);
  }
  return [...f.querySelectorAll('input.import:checked')].map(c => c.name);
})(["<ID1>", "<ID2>"], [])
```

Danach den Button „Aktivitäten importieren“ anklicken (per `find` die Referenz holen und klicken) und die Folgeseite auf Fehlermeldungen prüfen. Anschließend die Zeilen erneut auslesen: importierte Zeilen sind jetzt `done: true`.

Die Seite ordnet Sportarten selbst zu (Walk → „Alternative Sportarten“, VirtualRide → „Rad fahren“ usw.).

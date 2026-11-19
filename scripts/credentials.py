"""Passwörter für die automatische Neu-Anmeldung aus dem Passwort-Speicher des Systems lesen.

Nutzt die Bibliothek `keyring` (macOS-Schlüsselbund, Windows-Anmeldeinformationsverwaltung,
Linux Secret Service). Der Nutzer legt die Einträge selbst an, z. B.:

    python3 -m keyring set strava-winter-sync-rse <benutzername>

Ohne `keyring` wird unter macOS ersatzweise das Kommando `security` benutzt.
Gibt es keinen Eintrag, liefert get_password() None – dann bleibt es bei der manuellen Anmeldung.
"""
import subprocess
import sys


def get_password(service, username):
    if not username:
        return None
    try:
        import keyring
        return keyring.get_password(service, username)
    except ImportError:
        pass
    except Exception as e:  # z. B. kein Backend verfügbar
        print(f"WARN: keyring: {e}", file=sys.stderr)
        return None
    if sys.platform == "darwin":
        r = subprocess.run(["security", "find-generic-password", "-s", service, "-a", username, "-w"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.rstrip("\n")
    return None

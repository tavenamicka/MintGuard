# MintGuard — Installationsanleitung

[Français](INSTALLATION.md) · [English](INSTALLATION.en.md) · [Español](INSTALLATION.es.md)

## Installation für Eltern (keine Vorkenntnisse nötig)

Diese Anleitung führt Sie Schritt für Schritt. Wenn etwas nicht wie erwartet funktioniert, springen Sie zu „Wenn etwas nicht klappt“ weiter unten: Keine dieser Situationen ist schlimm, und es kann nichts kaputtgehen.

**Bevor Sie beginnen**, prüfen Sie Folgendes:
- Ihr Computer läuft mit **Linux Mint** (oder Ubuntu) und ist mit dem Internet verbunden;
- Sie kennen das **Passwort**, mit dem Sie sich anmelden;
- jedes Kind hat **sein eigenes Benutzerkonto** auf dem Computer.

### Schritt 1 — Installationsdatei herunterladen

1. Öffnen Sie die [Seite mit den MintGuard-Versionen](https://github.com/tavenamicka/MintGuard/releases/latest).
2. Scrollen Sie zum Bereich **„Assets“**.
3. Klicken Sie auf `mintguard_0.1.1-1_all.deb` (oder eine höhere Nummer). Diese Datei ist das „Installationsprogramm“: Die Endung `.deb` wird unter Linux Mint für Installationsprogramme verwendet.

Die Datei wird im Ordner **Downloads** gespeichert.

### Schritt 2 — Installieren

1. Öffnen Sie den Ordner **Downloads** und doppelklicken Sie auf die Datei `mintguard…deb`.
2. Ein Fenster der Softwareverwaltung öffnet sich. Klicken Sie auf **Installieren**.
3. Geben Sie Ihr Passwort ein und bestätigen Sie. Warten Sie bis zum Ende, etwa eine Minute.

*Der Doppelklick bewirkt nichts?* Klicken Sie mit der rechten Maustaste auf die Datei, dann auf **Öffnen mit** und **GDebi-Paketinstallation**. Funktioniert auch das nicht, verwenden Sie die weiter unten beschriebene **andere Methode**.

### Schritt 3 — MintGuard öffnen

Klicken Sie auf das Menü des Computers (unten links), tippen Sie „MintGuard“ und klicken Sie auf das Symbol.

### Schritt 4 — Fragen des Assistenten beantworten

Beim ersten Start führt MintGuard Sie durch die Einrichtung. Es fragt nach:
- dem **Vornamen** Ihres Kindes und dem **Namen seines Benutzerkontos** auf dem Computer;
- einem **Profil** je nach Alter (6–12 oder 13–18 Jahre): Sie können danach alles ändern;
- einem **PIN-Code** (4 oder mehr Ziffern). Notieren Sie ihn auf Papier und bewahren Sie ihn sicher auf: Er schützt Ihre Einstellungen, und Ihre Kinder dürfen ihn nicht kennen.

### Schritt 5 — Schutz aktivieren

Erscheint die Meldung **„Der Schutz ist noch nicht aktiv“**, klicken Sie auf **„Schutz jetzt aktivieren“** und geben Sie Ihr Passwort ein. Der Schutz läuft nun und startet mit dem Computer automatisch neu.

### Schritt 6 — Website-Sperre aktivieren

Erscheint die Meldung **„Die Website-Sperre funktioniert nicht“**, klicken Sie auf **„Website-Sperre aktivieren“** und geben Sie Ihr Passwort ein. Ihr Computer nutzt nun MintGuard, um Websites zu finden: Nur so können die von Ihnen gewählten Seiten gesperrt werden. Ohne diesen Schritt funktionieren die Zeitlimits, aber keine Website wird gesperrt.

Wie es weitergeht (Zeitfenster festlegen, Websites oder Apps sperren), lesen Sie im Handbuch: [Français](USER_MANUAL_FR.md) · [English](USER_MANUAL_EN.md) · [Deutsch](USER_MANUAL_DE.md) · [Español](USER_MANUAL_ES.md).

### Andere Methode: Installation über das Terminal

Nur verwenden, wenn der Doppelklick nicht funktioniert. Das **Terminal** ist ein Fenster, in dem man dem Computer Anweisungen durch Eintippen gibt.

1. Drücken Sie gleichzeitig die Tasten `Strg`, `Alt` und `T`: Das Terminal öffnet sich.
2. Kopieren Sie diese Zeile hinein und drücken Sie die `Eingabetaste`:

```bash
cd ~/Downloads
```

3. Kopieren Sie diese Zeile hinein und drücken Sie die `Eingabetaste`:

```bash
sudo apt install ./mintguard_0.1.0-1_all.deb
```

4. Das Terminal fragt nach Ihrem Passwort. **Beim Tippen erscheint nichts, nicht einmal Punkte: Das ist normal.** Tippen Sie es trotzdem und drücken Sie die `Eingabetaste`.
5. Werden Sie um eine Bestätigung gebeten, tippen Sie `J` und die `Eingabetaste`. Warten Sie, bis die Zeile mit `$` am Ende wieder erscheint: Die Installation ist abgeschlossen.

(`sudo` bedeutet „als Administrator ausführen“, und `apt` ist das Werkzeug, das unter Linux Mint Programme installiert.)

### MintGuard aktualisieren

**Welche Version haben Sie?** Sie steht im Titel des MintGuard-Fensters, zum Beispiel „MintGuard 0.1.1“. Steht im Titel nur „MintGuard“, haben Sie Version 0.1.0. Die Neuerungen jeder Version stehen auf der [Seite mit den Versionen](https://github.com/tavenamicka/MintGuard/releases) und im [Änderungsprotokoll](../CHANGELOG.en.md) (auf Englisch).

**Zum Aktualisieren** wiederholen Sie die Schritte 1 und 2 mit der neuen Datei: herunterladen, doppelklicken, auf **Installieren** (oder **Aktualisieren**) klicken und Ihr Passwort eingeben. Die alte Version muss nicht deinstalliert werden: Ihre Kinder, ihre Zeitpläne, gesperrte Websites und Apps sowie Ihr PIN-Code bleiben erhalten.

**Nach der Aktualisierung** öffnen Sie MintGuard. Bietet eine Karte „Schutz jetzt aktivieren“ oder „Website-Sperre aktivieren“ an, klicken Sie darauf und geben Sie Ihr Passwort ein. Das ist beim Wechsel von 0.1.0 auf 0.1.1 der Fall; ab 0.1.1 startet der Schutz nach jeder Aktualisierung von selbst neu.

Im Terminal, im Ordner Downloads: `sudo apt install ./mintguard_0.1.1-1_all.deb` (ersetzen Sie die Nummer durch die der heruntergeladenen Datei).

### Wenn etwas nicht klappt

| Was Sie sehen | Was passiert | Was zu tun ist |
|---|---|---|
| MintGuard erscheint nicht im Menü | Das Menü wurde noch nicht aktualisiert. | Melden Sie sich ab und wieder an oder starten Sie den Computer neu. |
| Eine Meldung erwähnt „Abhängigkeiten“ oder ein fehlendes Paket | Der Computer konnte etwas, das MintGuard braucht, nicht herunterladen. | Prüfen Sie die Internetverbindung und versuchen Sie die Installation erneut. |
| Die Meldung „Der Schutz ist noch nicht aktiv“ kehrt zurück | Der Schutz wurde nicht gestartet. | Klicken Sie erneut auf „Schutz jetzt aktivieren“. Schlägt das fehl, öffnen Sie das Terminal und tippen Sie `sudo systemctl start mintguard-daemon`. |
| Die Meldung „Die Website-Sperre funktioniert nicht“ erscheint | Ihr Computer nutzt MintGuard noch nicht, um Websites zu finden. | Klicken Sie auf „Website-Sperre aktivieren“ und geben Sie Ihr Passwort ein. Schlägt das fehl, öffnen Sie das Terminal und tippen Sie `sudo /usr/lib/mintguard/switch-dns.sh`. |
| Sie haben den PIN-Code vergessen | Das passiert oft, und es gibt eine Lösung. | Klicken Sie im Code-Fenster auf „Code vergessen?“ (siehe Benutzerhandbuch). |
| Sie möchten deinstallieren | — | Tippen Sie im Terminal `sudo apt remove mintguard` (Ihre Einstellungen bleiben erhalten) oder `sudo apt purge mintguard` (alles wird gelöscht). |

Löst nichts davon Ihr Problem, fragen Sie die Person, die Ihnen MintGuard empfohlen hat, oder eröffnen Sie eine Anfrage auf der [Seite für Probleme](https://github.com/tavenamicka/MintGuard/issues).

---

Entwickler und Administratoren: Die technische Installation (Paket bauen, Entwicklungsumgebung) steht in der [französischen Anleitung](INSTALLATION.md#installation-technique-développeurs-et-administrateurs).

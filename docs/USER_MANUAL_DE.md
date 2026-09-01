# MintGuard — Benutzerhandbuch

*Damit Ihre Kinder das Internet sicher entdecken können.*

Dieses Handbuch richtet sich an Eltern. Für die technische Installation siehe [INSTALLATION.md](INSTALLATION.md).

---

## 1. Was ist MintGuard?

MintGuard ist eine Kindersicherungs-Anwendung für Linux Mint. Sie besteht aus zwei Teilen:

- **Ein Überwachungsprogramm**, das mit dem Computer startet und Ihre Regeln durchgehend anwendet, auch wenn Sie das Hauptfenster nie öffnen.
- **Ein Einstellungsfenster** (das Sie öffnen, um Einstellungen zu ändern und Berichte anzusehen): Dieses Handbuch beschreibt genau dieses Fenster.

MintGuard kann:
- **Webseiten blockieren** (soziale Netzwerke, Online-Spiele, Unterhaltung, oder jede Seite, die Sie selbst hinzufügen).
- **Anwendungen blockieren** (Spiele, Messenger usw.).
- **Nutzungszeiten begrenzen**, mit automatischer Sitzungsschließung außerhalb der erlaubten Zeiten.
- **Eine wöchentliche Zusammenfassung** der blockierten Inhalte anzeigen.

**Wichtige Voraussetzung**: MintGuard geht davon aus, dass jedes Kind **ein eigenes Linux-Benutzerkonto** auf dem Computer hat (kein gemeinsames Konto mit Ihnen oder zwischen Kindern). Über dieses Konto weiß MintGuard, wer den Computer gerade nutzt.

---

## 2. Erster Start: der Einrichtungsassistent

Beim ersten Start führt Sie ein Assistent in 6 Schritten:

1. **Willkommen** — eine kurze Einführung.
2. **Welches Kind möchten Sie schützen?** — der Vorname des Kindes (zur Anzeige) und sein **Linux-Benutzername** (der Kontoname, nicht der Vorname — fragen Sie einen Techniker, falls Sie ihn nicht kennen).
3. **Schnelleinrichtung** — zwei fertige Profile je nach Alter:
   - **6-12 Jahre**: 2 Stunden Zugang pro Tag, soziale Netzwerke und Online-Spiele blockiert.
   - **13-18 Jahre**: 3 Stunden Zugang pro Tag, große soziale Netzwerke eingeschränkt (TikTok, Instagram, Snapchat).
   Sie können später alles in den Einstellungen ändern — dies sind nur Ausgangspunkte.
4. **PIN-Code** — ein 4-stelliger Code (bis zu 8 Stellen), der den Zugriff auf Einstellungen und Berichte schützt. **Notieren Sie ihn sicher**: siehe Abschnitt [Sicherheit und Datenschutz](#5-sicherheit-und-datenschutz), was passiert, wenn Sie ihn vergessen.
5. **So funktioniert's** — eine visuelle Erinnerung an das Prinzip (MintGuard beobachtet, wendet Regeln an, informiert Sie).
6. **Fertig!** — der Schutz ist aktiv, weiter geht's zum Dashboard.

---

## 3. Das Dashboard

Dies ist der Hauptbildschirm, der bei jedem Start der Anwendung geöffnet wird.

- **Kinderauswahl**: Wenn Sie mehrere Kinder eingerichtet haben, wählen Sie aus, welches angezeigt werden soll.
- **Schutzstatus**: `AKTIV`, wenn mindestens eine Regel (Zeit oder blockierte Seite) für dieses Kind konfiguriert ist, sonst `INAKTIV`.
- **Heutiges Zeitfenster**: die heute für das ausgewählte Kind erlaubten Zeiten, oder „Heute freier Zugang", wenn für diesen Tag keine Regel festgelegt ist.
- **Letzte Einschränkung**: das zuletzt aufgezeichnete Ereignis (blockierte Anwendung oder erreichtes Zeitlimit).
- **Schaltflächen Einstellungen / Berichte**: fragen vor dem Öffnen nach Ihrem PIN-Code.

---

## 4. Einstellungen ändern

Ein Klick auf **Einstellungen** fragt nach Ihrem PIN-Code und öffnet dann drei Reiter.

### Reiter Zeit

Für jeden Wochentag: ein Zeitfenster aktivieren/deaktivieren und Start- und Endzeit festlegen. Außerhalb dieses Fensters **schließt sich die Sitzung des Kindes automatisch** (ohne vorherige Warnung — informieren Sie Ihr Kind im Voraus über diese Regel). Ein Tag ohne aktiviertes Zeitfenster bedeutet freien Zugang an diesem Tag.

Änderungen werden erst nach Klick auf **Speichern** wirksam.

### Reiter Webseiten

Ankreuzbare Kategorien (Soziale Netzwerke, Unterhaltung, Online-Spiele) und eine eigene Seitenliste, die Sie frei hinzufügen/entfernen können (z. B. `tiktok.com`).

**Wichtig**: Anders als bei den Zeitplänen gilt die Seitenblockierung für den **gesamten Computer**, nicht nur für das ausgewählte Kinderkonto — da ein einziges DNS-Blockiersystem die gesamte Maschine abdeckt. Wenn sich mehrere Kinder denselben Computer teilen, teilen sie sich dieselbe Liste blockierter Seiten.

Änderungen in diesem Reiter werden **ohne Speichern-Schaltfläche** übernommen — rechnen Sie aber mit bis zu etwa dreißig Sekunden, bevor die Blockierung tatsächlich wirksam wird (die Zeit, die der Hintergrunddienst braucht, um die Liste neu einzulesen).

### Reiter Anwendungen

Vier vorgeschlagene Anwendungen (Firefox, Chrome, Discord, Steam) zum Ankreuzen, plus eine eigene Liste für weitere Programmnamen. Eine bereits laufende blockierte Anwendung wird innerhalb weniger Sekunden automatisch geschlossen. Wie bei Webseiten gilt dies für den gesamten Computer.

---

## 5. Sicherheit und Datenschutz

- **Der PIN-Code** schützt den Zugriff auf Einstellungen und Berichte. Er wird sicher gespeichert (nie im Klartext).
- **PIN vergessen?** Klicken Sie im Eingabefenster auf „PIN vergessen?". MintGuard bittet Sie, sich mit **dem Passwort Ihres eigenen Kontos** zu bestätigen (das, mit dem Sie sich an diesem Computer anmelden) — über ein Systemfenster, wie es zum Beispiel beim Installieren eines Updates erscheint. Dieses Passwort wird niemals von MintGuard selbst verwaltet oder gespeichert. Nach der Bestätigung können Sie sofort einen neuen PIN festlegen.
- Die Aktivitätsprotokolle und die Datenbank von MintGuard sind nur für ein Administratorkonto lesbar — Ihr Kind hat keinen Zugriff darauf, selbst wenn es weiß, wo es suchen muss.

---

## 6. Die Berichte

Der Reiter **Berichte** (PIN-geschützt) zeigt für die letzten 7 Tage und pro Kind:
- Blockierte Anwendungen und wie oft jede geschlossen wurde.
- Wie oft das Zeitlimit erreicht wurde (automatische Sitzungsschließung).

**MintGuard zeigt keine „insgesamt genutzte Bildschirmzeit" an**: Die Anwendung misst nicht durchgehend die Sitzungsdauer, sondern nur Blockierungsereignisse. Dies ist eine bewusste Entscheidung — anstatt eine ungefähre Zahl zu erfinden, zeigen wir lieber nichts an, was Sie nicht selbst vollständig überprüfen könnten.

---

## 7. Was MintGuard nicht tut (Grenzen, die Sie kennen sollten)

Um ehrlich zu bleiben, was der Schutz tatsächlich abdeckt:

- **Keine automatische Filterung „jugendgefährdender Inhalte".** Eine zuverlässige Filterung würde eine von Dritten gepflegte, regelmäßig aktualisierte Seitenliste erfordern, die MintGuard derzeit nicht enthält. Sie können manuell Seiten im Reiter Webseiten hinzufügen.
- **Ein technisch versiertes Kind könnte versuchen, die Blockierung zu umgehen**, indem es einen verschlüsselten DNS-Dienst („DNS-over-HTTPS") direkt im Browser konfiguriert. MintGuard blockiert den Wechsel zu einem anderen klassischen DNS-Resolver, aber nicht diese fortgeschrittenere Methode.
- **Die Anwendungsblockierung basiert auf dem Programmnamen**, nicht auf einer tieferen Systemkontrolle — eine umbenannte Anwendung könnte unbemerkt bleiben.
- **MintGuard setzt ein eigenes Linux-Konto pro Kind voraus.** Wenn Ihr Kind Ihre eigene Sitzung oder eine gemeinsame Sitzung nutzt, greift der Schutz nicht korrekt.
- **Ein Computer = eine gemeinsame Liste blockierter Seiten** für alle Kinder, die ihn nutzen (siehe Abschnitt Webseiten oben).

Diese Einschränkungen werden absichtlich dokumentiert statt verschwiegen: Es ist besser zu wissen, was der Schutz tatsächlich abdeckt.

---

## 8. Brauchen Sie Hilfe?

- Jeder Bildschirm hat **„?"**-Schaltflächen mit einer einfachen Erklärung in Alltagssprache.
- Bei einem technischen Problem (Installation, Daemon startet nicht) siehe [INSTALLATION.md](INSTALLATION.md) oder wenden Sie sich an die Person, die MintGuard für Sie installiert hat.

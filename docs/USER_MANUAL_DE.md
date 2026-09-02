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
6. **Fertig!** — Ihre Einstellungen sind gespeichert, weiter geht's zum Dashboard.

**Möglicher letzter Schritt**: Wenn das Dashboard das Banner **„Der Schutz ist noch nicht aktiv"** anzeigt, klicken Sie auf **„Schutz jetzt aktivieren"**. Es öffnet sich ein einziges Systemfenster zur Bestätigung (Ihr übliches Passwort) — danach läuft der Schutz wirklich, auch bei geschlossenem Hauptfenster. Dieses Banner erscheint danach normalerweise nicht mehr (der Schutz startet von selbst mit dem Computer), außer bei einem Systemproblem — klicken Sie dann einfach erneut darauf.

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

Für jeden Wochentag: ein Zeitfenster aktivieren/deaktivieren und Start- und Endzeit festlegen. Außerhalb dieses Fensters **schließt sich die Sitzung des Kindes automatisch**. Ein Symbol im Benachrichtigungsbereich des Kindes warnt einige Minuten vorher (10, 5, dann 1 Minute) und meldet geschlossene, nicht erlaubte Anwendungen — eine informative Warnung, nicht garantiert (abhängig von der Systray-Unterstützung der Arbeitsumgebung): informieren Sie Ihr Kind dennoch im Voraus über diese Regel. Ein Tag ohne aktiviertes Zeitfenster bedeutet freien Zugang an diesem Tag.

In dem Moment, in dem die Zeit abgelaufen ist, wird Ihr Kind **nicht ohne Vorwarnung abgemeldet**: Ein Fenster erscheint im Vordergrund mit einem Countdown (etwa 1 bis 2 Minuten), das dazu auffordert, die Arbeit zu speichern, bevor die Sitzung tatsächlich geschlossen wird. Anders als das Systray-Popup erscheint dieses Fenster immer, unabhängig von der verwendeten Arbeitsumgebung.

**Nutzungszeit pro Tag begrenzen**: Zusätzlich zum Zeitfenster können Sie „Nutzungszeit pro Tag begrenzen" aktivieren, um die insgesamt genutzten Minuten pro Tag zu begrenzen (z. B. 120 Min/Tag), selbst wenn das Zeitfenster selbst größer ist. Sobald dieses Kontingent erreicht ist, schließt sich die Sitzung des Kindes automatisch für den Rest des Tages — genau wie beim Verlassen des Zeitfensters. Am nächsten Tag beginnt das Kontingent wieder von vorn.

Änderungen werden erst nach Klick auf **Speichern** wirksam.

### Reiter Webseiten

Ankreuzbare Kategorien (Soziale Netzwerke, Unterhaltung, Online-Spiele) und eine eigene Seitenliste, die Sie frei hinzufügen/entfernen können (z. B. `tiktok.com`).

**Wichtig**: Anders als bei den Zeitplänen gilt die Seitenblockierung für den **gesamten Computer**, nicht nur für das ausgewählte Kinderkonto — da ein einziges DNS-Blockiersystem die gesamte Maschine abdeckt. Wenn sich mehrere Kinder denselben Computer teilen, teilen sie sich dieselbe Liste blockierter Seiten.

**Was Ihr Kind tatsächlich sieht**: MintGuard zeigt keine Seite „Diese Seite ist gesperrt" an. Die Sperrung erfolgt auf Netzwerkebene (DNS), noch bevor die Seite überhaupt zu laden beginnt — Ihr Kind sieht daher die übliche Fehlerseite seines Browsers, etwa „Verbindung nicht möglich" oder „Diese Seite ist nicht erreichbar". Das ist normal: Es bedeutet, dass die Sperre funktioniert, nicht dass ein technisches Problem vorliegt. Es lohnt sich, dies Ihrem Kind im Voraus zu erklären, damit es versteht, dass eine solche Meldung eine von Ihnen gesetzte Grenze ist und kein Internetausfall.

Änderungen in diesem Reiter werden **ohne Speichern-Schaltfläche** übernommen — rechnen Sie aber mit bis zu etwa dreißig Sekunden, bevor die Blockierung tatsächlich wirksam wird (die Zeit, die der Hintergrunddienst braucht, um die Liste neu einzulesen).

### Reiter Anwendungen

Auf dem Computer installierte Anwendungen werden automatisch erkannt und nach Kategorie zum Ankreuzen angeboten, plus eine eigene Liste für weitere Programmnamen. Eine bereits laufende blockierte Anwendung wird innerhalb weniger Sekunden automatisch geschlossen. Wie bei Webseiten gilt dies für den gesamten Computer.

**Nutzungszeit pro Tag begrenzen (statt vollständiger Sperre)**: Für eine angekreuzte Anwendung können Sie „Nutzungszeit pro Tag begrenzen" aktivieren, statt sie vollständig zu sperren. Ihr Kind kann sie dann bis zu der von Ihnen festgelegten Minutenzahl pro Tag nutzen (z. B. 30 Min/Tag); sobald diese Zeit überschritten ist, schließt sich die Anwendung automatisch und lässt sich bis zum nächsten Tag nicht mehr öffnen.

---

## 5. Sicherheit und Datenschutz

- **Der PIN-Code** schützt den Zugriff auf Einstellungen und Berichte. Er wird sicher gespeichert (nie im Klartext).
- **PIN vergessen?** Klicken Sie im Eingabefenster auf „PIN vergessen?". MintGuard zeigt zunächst eine Meldung, die erklärt, was als Nächstes passiert, bevor sich ein Systemfenster öffnet — damit dieses Fenster keine Überraschung ist. Sie müssen sich dann über dieses Systemfenster mit **dem Passwort Ihres eigenen Kontos** bestätigen (das, mit dem Sie sich an diesem Computer anmelden) — wie es zum Beispiel beim Installieren eines Updates erscheint. Dieses Passwort wird niemals von MintGuard selbst verwaltet oder gespeichert. Nach der Bestätigung können Sie sofort einen neuen PIN festlegen.
- Die Aktivitätsprotokolle und die Datenbank von MintGuard sind nur für ein Administratorkonto lesbar — Ihr Kind hat keinen Zugriff darauf, selbst wenn es weiß, wo es suchen muss.

---

## 6. Die Berichte

Der Reiter **Berichte** (PIN-geschützt) zeigt für die letzten 7 Tage und pro Kind:
- Blockierte Anwendungen und wie oft jede geschlossen wurde.
- Wie oft das Zeitlimit erreicht wurde (automatische Sitzungsschließung) — ob durch Verlassen des erlaubten Zeitfensters oder durch Überschreiten eines täglichen Minutenkontingents.

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

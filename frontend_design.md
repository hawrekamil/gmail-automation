Entwickle ein hochmodernes Frontend für ein Gmail-Automatisierungstool mit Angular.

Ziel:
Das Frontend soll eine professionelle Web-App sein, mit der Nutzer Gmail-Ordner/Labels durchsuchen, E-Mails anzeigen, nach Absender filtern und Massenaktionen wie “in Papierkorb verschieben” oder “endgültig löschen” sicher ausführen können.

Technologie:
- Angular mit TypeScript
- Moderne Angular-Struktur mit Components, Services und Routing
- Responsive Design für Desktop, Tablet und Mobile
- API-Kommunikation über einen zentralen GmailApiService
- Saubere State-Verwaltung innerhalb der Komponenten oder mit Signals/RxJS
- Formularvalidierung für Such- und Filterfelder

Design-Stil:
Das UI soll modern, klar und produktiv wirken, ähnlich einer hochwertigen SaaS-Dashboard-App. Kein verspieltes Landingpage-Design, sondern ein fokussiertes Arbeitswerkzeug.

Visuelle Richtung:
- Heller, ruhiger Hintergrund
- Klare Seitennavigation links
- Hauptbereich mit Tabellen-/Listenansicht
- Dezente Schatten, feine Border, großzügige Abstände
- Moderne Typografie
- Akzentfarbe: Blau oder Indigo für primäre Aktionen
- Warnfarben klar unterscheiden:
  - Gelb/Orange für “Papierkorb”
  - Rot für “Endgültig löschen”
  - Grün für erfolgreiche Aktionen
- Keine überladenen Kartenlayouts
- Keine grellen Verläufe
- Keine dekorativen Illustrationen

Layout:
1. Sidebar
   - App-Name: “Gmail Automation”
   - Navigation:
     - Dashboard
     - Ordner / Labels
     - E-Mails
     - Absender-Filter
     - Batch-Aktionen
     - Einstellungen

2. Topbar
   - Aktueller Gmail-Account
   - Suchfeld
   - Refresh-Button
   - Statusanzeige für Verbindung/Auth

3. Dashboard
   - Übersicht über:
     - Gesamtzahl E-Mails
     - Ungelesene E-Mails
     - Labels/Ordner
     - Letzte Batch-Aktion
   - Schnelle Aktionen:
     - Posteingang öffnen
     - Spam öffnen
     - Papierkorb öffnen

4. Ordner-/Label-Ansicht
   - Liste aller Gmail-Labels
   - Jeder Ordner zeigt:
     - Name
     - ID
     - Anzahl E-Mails, falls verfügbar
     - Button “Öffnen”
   - Beim Öffnen eines Ordners:
     - E-Mail-Liste anzeigen
     - Aktionen:
       - Alle E-Mails in Papierkorb verschieben
       - Alle E-Mails endgültig löschen
       - E-Mails von bestimmtem Absender filtern
       - Gefilterte E-Mails löschen

5. E-Mail-Liste
   - Tabellenartige Ansicht mit:
     - Checkbox
     - Status ungelesen/gelesen
     - Betreff
     - Absender
     - Datum
     - Labels
   - Bulk-Auswahl
   - Aktionen für ausgewählte E-Mails:
     - Als gelesen markieren
     - Label anwenden
     - In Papierkorb verschieben
     - Endgültig löschen

6. Sicherheitsdialoge
   Für gefährliche Aktionen muss ein professioneller Confirm-Dialog erscheinen:
   - Titel: “Endgültig löschen?”
   - Beschreibung: “Diese Aktion kann nicht rückgängig gemacht werden.”
   - Anzahl betroffener E-Mails anzeigen
   - Optional Eingabe von “LÖSCHEN” oder “DELETE” zur Bestätigung bei großen Mengen
   - Primärer Button rot
   - Abbrechen-Button neutral

7. Absender-Filter
   - Eingabefeld für Name oder E-Mail-Adresse
   - Ordnerauswahl
   - Ergebnisliste
   - Aktionen:
     - Alle Treffer markieren
     - Treffer in Papierkorb verschieben
     - Treffer endgültig löschen

UX-Anforderungen:
- Ladezustände mit Skeletons oder Spinnern
- Leere Zustände klar darstellen
- Fehler verständlich anzeigen
- Erfolgs-/Fehlerstatistik nach Batch-Aktionen anzeigen:
  - Gesamt
  - Erfolgreich
  - Fehlgeschlagen
  - Erfolgsrate
- Kein falscher Erfolg anzeigen, wenn 0 Aktionen erfolgreich waren
- Große Löschaktionen müssen klar und vorsichtig gestaltet sein
- UI soll schnell bedienbar und nicht wie eine Marketing-Seite wirken

Komponenten-Vorschlag:
- AppShellComponent
- SidebarComponent
- TopbarComponent
- DashboardComponent
- LabelListComponent
- EmailListComponent
- EmailTableComponent
- SenderFilterComponent
- BatchActionDialogComponent
- ConfirmDeleteDialogComponent
- StatusToastComponent
- EmptyStateComponent
- LoadingStateComponent

API-Service-Vorschlag:
Erstelle einen GmailApiService mit Methoden wie:
- getProfile()
- getLabels()
- getEmailsByLabel(labelId)
- getAllMessageIds(labelId)
- filterEmailsBySender(labelId, sender)
- markAsRead(messageIds)
- applyLabel(messageIds, labelId)
- trashEmails(messageIds)
- deleteEmails(messageIds)

Qualitätsanforderungen:
- Sauberer, wartbarer Angular-Code
- Typisierte Interfaces für API-Daten
- Wiederverwendbare UI-Komponenten
- Responsives Layout
- Accessibility beachten:
  - Tastaturbedienung
  - Fokuszustände
  - ARIA für Dialoge
  - Gute Kontraste
- Keine sensiblen Tokens im Frontend speichern
- Backend-API muss die Gmail-Authentifizierung übernehmen

Ergebnis:
Erstelle eine moderne Angular-Web-App, die wie ein professionelles Gmail-Admin-Dashboard wirkt und alle wichtigen Workflows sicher, klar und effizient abbildet.

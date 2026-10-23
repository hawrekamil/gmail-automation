# Label/Ordner Navigation & E-Mail Filterung 📂

Zwei Interfaces zum Verwalten und Filtern von Gmail-E-Mails:

## 1. Interaktives Menü (`main.py`) 🎯

Ein benutzerfreundliches Menü-System ohne Kommandozeilen-Kommandos.

### Starten
```bash
python main.py
```

### Hauptmenü-Optionen

```
[1] Profil anzeigen
    └─ Zeigt Email, Nachrichten-Anzahl, Threads

[2] Labels/Ordner anzeigen
    └─ Listet alle verfügbaren Labels auf
    └─ Kategorisiert in "Häufig" und "Benutzerdefiniert"

[3] E-Mails in einem Ordner auflisten
    └─ Wähle Label → Zeige bis zu 20 E-Mails
    └─ Mit Status (Neu/Gelesen), Betreff, Absender, Datum

[4] E-Mails nach Absender filtern
    └─ Wähle Label → Eingabe Absendername/Email
    └─ Zeige alle passenden E-Mails

[5] Letzte 5 E-Mails aus Posteingang
    └─ Schnellanzeige für Posteingang

[0] Beenden
```

### Vordefinierte Labels

| Taste | Label | Name |
|-------|-------|------|
| [1] | INBOX | 📥 Posteingang |
| [2] | SNOOZED | ⏰ Snooze |
| [3] | SOCIAL | 👥 Sozial |
| [4] | UPDATES | 🔔 Updates |
| [5] | PROMOTIONS | 🎉 Promotions |
| [6] | SPAM | 🚫 Spam |
| [7+] | Benutzerdefiniert | ✨ Custom Labels |

### Beispiel-Nutzung (Interaktiv)

```
Menü: [3] E-Mails in einem Ordner auflisten
  Label wählen: [1]
  
  → Zeigt 20 E-Mails aus INBOX:
    [🔴 NEU]  1. Re: Projekt Update
                Von: boss@company.com
                Datum: 2026-05-08 09:30
    
    [   ]     2. Newsletter Mai
                Von: newsletter@example.com
                Datum: 2026-05-07 15:45
```

---

## 2. Kommandozeilen-Interface (`cli.py`) ⚡

Direkte Kommandos für Scripting und Automation.

### Starten

```bash
# Hilfe anzeigen
python cli.py --help

# Spezifischen Befehl ausführen
python cli.py <befehl> [optionen]
```

### Verfügbare Befehle

#### `list-labels` – Labels auflisten
```bash
python cli.py list-labels
```

**Output:**
```
----------------------------------------------------------------------
  📂 Verfügbare Labels
----------------------------------------------------------------------

  ID                   Name
  ----------------------------------------------------------
  INBOX                Posteingang
  SNOOZED              Snooze
  SOCIAL               Sozial
  UPDATES              Updates
  PROMOTIONS           Promotions
  ...
```

---

#### `show-profile` – Profil anzeigen
```bash
python cli.py show-profile
```

**Output:**
```
----------------------------------------------------------------------
  📊 Gmail Profil
----------------------------------------------------------------------

  Email:           max.mustermann@gmail.com
  Nachrichten:     1234
  Threads:         567
```

---

#### `list-emails` – E-Mails auflisten
```bash
python cli.py list-emails --label INBOX --max 10
```

**Optionen:**
- `--label` – Label-ID (default: INBOX)
- `--max` – Maximale Anzahl (default: 10, max: 100)

**Output:**
```
----------------------------------------------------------------------
  📧 E-Mails in 'INBOX'
----------------------------------------------------------------------

  Gefunden: 10 E-Mail(s)

  #   Status   Betreff                         Von
  ----------------------------------------------------------
  1   🔴 NEU   Re: Projekt Update             boss@company.com
  2   ✓        Newsletter Mai                 newsletter@example.com
  3   🔴 NEU   Willkommen bei...              info@service.com
```

**Beispiele:**
```bash
# Posteingang (Standard)
python cli.py list-emails

# Letzte 20 E-Mails aus Spam
python cli.py list-emails --label SPAM --max 20

# Benutzerdefiniertes Label
python cli.py list-emails --label "LabelName" --max 5
```

---

#### `filter-emails` – Nach Absender filtern
```bash
python cli.py filter-emails --label INBOX --sender "boss@company.com"
```

**Optionen:**
- `--label` – Label-ID (default: INBOX)
- `--sender` – Absendername oder Email (erforderlich)

**Output:**
```
----------------------------------------------------------------------
  🔍 E-Mails von 'boss@company.com' in 'INBOX'
----------------------------------------------------------------------

  Gefunden: 5 E-Mail(s)

  [🔴 NEU] Re: Projekt Update
       Von:   boss@company.com
       Datum: 2026-05-08 09:30
  
  [   ] Meeting Termin
       Von:   boss@company.com
       Datum: 2026-05-07 16:00
```

**Beispiele:**
```bash
# Alle E-Mails von spezifischer Email
python cli.py filter-emails --sender "john@example.com"

# Alle E-Mails von Person (Partial Match)
python cli.py filter-emails --sender "john"

# In spezifischem Label
python cli.py filter-emails --label SOCIAL --sender "twitter"

# Aus Spam-Ordner
python cli.py filter-emails --label SPAM --sender "@offers"
```

---

#### `delete-emails-by-sender` – E-Mails ENDGÜLTIG löschen 🗑️
```bash
python cli.py delete-emails-by-sender --label INBOX --sender "spam@evil.com"
```

**Optionen:**
- `--label` – Label-ID (default: INBOX)
- `--sender` – Absendername oder Email (erforderlich)
- `--confirm` – Überspringe Bestätigungsfrage (optional, Vorsicht!)

**Output:**
```
----------------------------------------------------------------------
  🗑️  Löschen von E-Mails aus 'INBOX'
----------------------------------------------------------------------

  🔍 Gefunden: 10 E-Mail(s) von 'spam@evil.com'

  Vorschau (erste 5):
    1. Unglaubliches Angebot!!
       2026-05-08 10:00
    2. KOSTENLOS!!!
       2026-05-07 15:30
    ...und 5 weitere

  ⚠️  Wirklich 10 E-Mail(s) löschen? (ja/nein): ja

  ✅ Erfolg:      10 E-Mail(s) gelöscht
  ❌ Fehler:      0 E-Mail(s)
  📊 Rate:        100%
```

**⚠️ WICHTIG: Diese Aktion kann NICHT rückgängig gemacht werden!**

**Beispiele:**
```bash
# Mit Bestätigung (normal - sicherer!)
python cli.py delete-emails-by-sender --label SPAM --sender "offers@spam.com"

# Ohne Bestätigung (automatisiert, aber Vorsicht!)
python cli.py delete-emails-by-sender --label PROMOTIONS --sender "newsletter" --confirm

# Alle E-Mails von Absender aus allen Labels
python cli.py delete-emails-by-sender --sender "hacker@malicious.com"
```

---

#### `trash-emails-by-sender` – E-Mails in Papierkorb verschieben (sicherer!) 🗑️
```bash
python cli.py trash-emails-by-sender --label INBOX --sender "spam@evil.com"
```

**Optionen:**
- `--label` – Label-ID (default: INBOX)
- `--sender` – Absendername oder Email (erforderlich)
- `--confirm` – Überspringe Bestätigungsfrage (optional)

**Output:**
```
----------------------------------------------------------------------
  🗑️  Verschiebe E-Mails in Papierkorb
----------------------------------------------------------------------

  🔍 Gefunden: 10 E-Mail(s) von 'spam@evil.com'

  ⚠️  10 E-Mail(s) in Papierkorb verschieben? (ja/nein): ja

  ✅ Erfolg:      10 E-Mail(s) in Papierkorb
  ❌ Fehler:      0 E-Mail(s)
  📊 Rate:        100%
```

**Vorteil:** E-Mails können noch 30 Tage lang wiederhergestellt werden!

**Beispiele:**
```bash
# Verschiebe in Papierkorb (Standard - am sichersten!)
python cli.py trash-emails-by-sender --label INBOX --sender "suspicious@domain.com"

# Automatisiert ohne Bestätigung
python cli.py trash-emails-by-sender --label SNOOZED --sender "old" --confirm
```

---

#### `batch-mark-read` – Alle als gelesen markieren ⚡
```bash
python cli.py batch-mark-read --label SNOOZED
```

**Optionen:**
- `--label` – Label-ID (default: INBOX)

**Output:**
```
----------------------------------------------------------------------
  📧 Markiere E-Mails in 'SNOOZED' als gelesen
----------------------------------------------------------------------

  ✅ Erfolg:      15 E-Mail(s)
  ❌ Fehler:      0 E-Mail(s)
  📊 Rate:        100%
```

**Beispiele:**
```bash
# Alle ungelesenen Promotions als gelesen markieren
python cli.py batch-mark-read --label PROMOTIONS

# Alle aus Snooze-Ordner
python cli.py batch-mark-read --label SNOOZED
```

---

#### `batch-apply-label` – Label anwenden ⚡
```bash
python cli.py batch-apply-label --source INBOX --target "Archive"
```

**Optionen:**
- `--source` – Quell-Label (default: INBOX)
- `--target` – Ziel-Label (erforderlich)

**Output:**
```
----------------------------------------------------------------------
  🏷️  Wende Label 'Archive' auf E-Mails an
----------------------------------------------------------------------

  ✅ Erfolg:      42 E-Mail(s)
  ❌ Fehler:      0 E-Mail(s)
  📊 Rate:        100%
```

**Beispiele:**
```bash
# Alle E-Mails aus Posteingang archivieren
python cli.py batch-apply-label --source INBOX --target "Archive"

# Alle Promotions mit Label versehen
python cli.py batch-apply-label --source PROMOTIONS --target "Marketing"

# Von Custom-Label zu anderem Label
python cli.py batch-apply-label --source "Important" --target "ToRead"
```

---

## Vergleich: Menü vs. CLI 🎯

| Feature | Menü (main.py) | CLI (cli.py) |
|---------|---|---|
| Benutzerfreundlich | ✅ Interaktiv | ⚡ Schnell |
| Lernkurve | 📚 Leicht | 🔧 Technisch |
| Scripting | ❌ Nein | ✅ Ja |
| Automation | ❌ Schwierig | ✅ Einfach |
| Cron-Jobs | ❌ Nein | ✅ Ja |
| Batch-Ops | ✅ Ja | ✅ Ja |

---

## Praktische Beispiele 💡

### Beispiel 1: Alle ungelesenen Promotions archivieren

**Interaktiv (main.py):**
```
[1] Labels anzeigen
[4] E-Mails nach Absender filtern
    → PROMOTIONS
    → (durchsuchen)
[3] E-Mails in Ordner
    → PROMOTIONS
```

**CLI (cli.py):**
```bash
python cli.py batch-apply-label --source PROMOTIONS --target "Archive"
```

---

### Beispiel 2: E-Mails von bestimmter Person finden

**Interaktiv (main.py):**
```
[4] E-Mails nach Absender filtern
    → INBOX
    → "john@company.com"
```

**CLI (cli.py):**
```bash
python cli.py filter-emails --label INBOX --sender "john@company.com"
```

---

### Beispiel 3: Automatisierte tägliche Aufgabe (Cron/Task Scheduler)

**Bash-Skript (automation.sh):**
```bash
#!/bin/bash
cd /path/to/gmail_automation_project

# Jeden Morgen um 9 Uhr
# 0 9 * * * /path/to/automation.sh

# Markiere alte Snoozed-E-Mails als gelesen
python cli.py batch-mark-read --label SNOOZED

# Archiviere E-Mails älter als 30 Tage
python cli.py batch-apply-label --source UPDATES --target "Archive"
```

---

### Beispiel 4: E-Mails von Absender LÖSCHEN

**Szenario:** "Alle Spam-E-Mails von 'spam@evil.com' löschen"

**Interaktiv (main.py):**
```
[4] E-Mails nach Absender filtern
    → Label: [6] (SPAM)
    → Absender: "spam@evil.com"
    → [3] In Papierkorb verschieben
       oder [4] Endgültig löschen
```

**CLI (cli.py) - mit Bestätigung (empfohlen!):**
```bash
# Erst in Papierkorb (sicherer - kann wieder hergestellt werden)
python cli.py trash-emails-by-sender --label SPAM --sender "spam@evil.com"

# Oder direkt löschen (mit Bestätigung)
python cli.py delete-emails-by-sender --label SPAM --sender "spam@evil.com"

# Oder ohne Bestätigung für Scripts
python cli.py delete-emails-by-sender --label SPAM --sender "spam@evil.com" --confirm
```

**Output:**
```
🔍 Gefunden: 25 E-Mail(s) von 'spam@evil.com'

Vorschau (erste 5):
  1. UNGLAUBLICHES ANGEBOT!!!
  2. KOSTENLOS!!!
  3. Sie haben gewonnen!!!
  ...und 22 weitere

⚠️  Wirklich 25 E-Mail(s) löschen? (ja/nein): ja

✅ Erfolg:      25 E-Mail(s) gelöscht
❌ Fehler:      0 E-Mail(s)
📊 Rate:        100%
```

---

### Beispiel 5: Sichere Newsletter-Bereinigung

**Workflow (empfohlen für wichtige Operationen):**

```bash
# Schritt 1: Finde Newsletter-E-Mails
python cli.py filter-emails --label PROMOTIONS --sender "newsletter"

# Schritt 2: Verschiebe erst in Papierkorb (nicht endgültig!)
python cli.py trash-emails-by-sender --label PROMOTIONS --sender "newsletter"

# Schritt 3: Nach 1 Woche prüfen, dann endgültig löschen
python cli.py delete-emails-by-sender --label TRASH --sender "newsletter" --confirm
```

---

## Fehlerbehandlung 🛡️

### Kein Label gefunden
```bash
$ python cli.py batch-apply-label --source INBOX --target "NonExistent"

❌ Label 'NonExistent' nicht gefunden
```

**Lösung:** Verwende `list-labels`, um gültiges Label-Name zu finden.

---

### Zu viele Anfragen (Rate Limit)
```bash
❌ Fehler: quotaExceeded
```

**Lösung:** Warte einige Sekunden und versuche erneut.

---

## Performance-Tipps ⚡

1. **Batch-Operationen verwenden** statt Einzeloperationen
   - 100 E-Mails markieren: `batch-mark-read` statt einzeln
   
2. **Caching aktivieren** (Standard)
   - Labels & Profile werden 10/30 Min. gecacht
   - Spart API-Calls!

3. **CLI für Automation** verwenden
   - Leichter zu scripten
   - Ideal für Cron-Jobs

---

## Häufig gestellte Fragen ❓

**F: Wie finde ich die Label-ID?**  
A: `python cli.py list-labels`

**F: Kann ich mehrere Filter kombinieren?**  
A: Derzeit einzeln, aber CLI erlaubt Scripting für Kombinationen.

**F: Funktioniert das mit Aliases und Subfoldern?**  
A: Ja! Gmail zeigt alles als Labels an.

**F: Wie automatisiere ich täglich?**  
A: Verwende CLI + Task Scheduler (Windows) oder Cron (Linux/Mac).

---

## Zusammenfassung 📝

✅ **Interaktives Menü** für explorative Nutzung  
✅ **CLI-Tool** für Automation & Scripting  
✅ **Label-Verwaltung** – Alle Labels einsehbar  
✅ **Filter nach Absender** – Schnelle Suche  
✅ **Batch-Operationen** – 90% weniger API-Calls  
✅ **Caching** – Schnellere Responses  

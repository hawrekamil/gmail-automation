# Delete/Trash E-Mails nach Absender 🗑️

Schnelle Referenz zum Löschen von E-Mails nach Absender.

## 🎯 Drei Sicherheitsstufen

### Level 1: Interaktives Menü (am sichersten)
```bash
python main.py
→ [4] E-Mails nach Absender filtern
  → Label wählen
  → Absender eingeben
  → [1] Als gelesen markieren
  → [2] Label anwenden
  → [3] In Papierkorb verschieben ← **Empfohlen!**
  → [4] Endgültig löschen ← **Irreversibel!**
```

**Vorteile:**
- ✅ Bestätigung vor jeder Aktion
- ✅ Vorschau der E-Mails
- ✅ Interaktiv und sicher

---

### Level 2: CLI mit Bestätigung (Standard)
```bash
# Verschiebe in Papierkorb (30 Tage Rettung)
python cli.py trash-emails-by-sender --label INBOX --sender "unwanted@domain.com"

# Endgültig löschen (mit Bestätigungsfrage)
python cli.py delete-emails-by-sender --label INBOX --sender "unwanted@domain.com"
```

**Workflow:**
```
🔍 Gefunden: 15 E-Mail(s)
⚠️  Wirklich 15 E-Mail(s) löschen? (ja/nein): 
```

**Vorteile:**
- ✅ Schneller als Menü
- ✅ Sicherheitsfrage vor Aktion
- ✅ Gut für Automation
- ✅ Kann scriptbar erweitert werden

---

### Level 3: CLI ohne Bestätigung (Automation)
```bash
# ⚠️  NUR für voll automatisierte Scripts!
python cli.py delete-emails-by-sender --label SPAM --sender "offers" --confirm
```

**Vorsicht:**
- ❌ Keine Bestätigung!
- ❌ Irreversibel!
- ✅ Ideal für tägliche Automation

---

## 📋 Checkliste vor dem Löschen

### Vor Level 1-2 (Mit Bestätigung)
- [ ] Absender korrekt eingegeben?
- [ ] Label korrekt? (INBOX, SPAM, SNOOZED, etc.)
- [ ] Vorschau der E-Mails gesehen?
- [ ] Wirklich alle löschen?

### Vor Level 3 (Ohne Bestätigung)
- [ ] Dasselbe wie oben
- [ ] + Script getestet mit `--label TRASH` (Test-Label)?
- [ ] + Nur im Cron-Job ohne `--confirm` aktiv?

---

## 🔄 Empfohlener Workflow für wichtige Operationen

```
Schritt 1: Filtern (TEST)
↓
python cli.py filter-emails --label INBOX --sender "sender@domain.com"

Schritt 2: In Papierkorb (SICHER)
↓
python cli.py trash-emails-by-sender --label INBOX --sender "sender@domain.com"

Schritt 3: Nach 1 Woche überprüfen
↓
python cli.py filter-emails --label TRASH --sender "sender@domain.com"

Schritt 4: Wenn alles ok, endgültig löschen
↓
python cli.py delete-emails-by-sender --label TRASH --sender "sender@domain.com"
```

---

## 💡 Praktische Beispiele

### 1. Spam direkt löschen (VORSICHT!)
```bash
# Interaktiv
python main.py → [4] → SPAM → [4] Endgültig löschen

# CLI
python cli.py delete-emails-by-sender --label SPAM --sender "offers@spam.com"
```

### 2. Unwollte Newsletter in Papierkorb (SICHER)
```bash
python cli.py trash-emails-by-sender --label PROMOTIONS --sender "newsletter@example.com"
```

### 3. Automatisierte Spam-Bereinigung
```bash
#!/bin/bash
# daily_cleanup.sh

# 1. Verschiebe verdächtige E-Mails in Papierkorb
python cli.py trash-emails-by-sender --label INBOX --sender "suspicious" --confirm

# 2. Verschiebe alte Promotions
python cli.py trash-emails-by-sender --label PROMOTIONS --sender "%" --confirm

# 3. Nach 3 Tagen: Löschen aus Papierkorb
sleep 259200  # 3 Tage

python cli.py delete-emails-by-sender --label TRASH --sender "%" --confirm
```

### 4. Absender blockieren & löschen
```bash
# 1. Finde alle E-Mails vom Absender
python cli.py filter-emails --label INBOX --sender "hacker@malicious.com"

# 2. Verschiebe in Papierkorb
python cli.py trash-emails-by-sender --label INBOX --sender "hacker@malicious.com"

# 3. Später: Endgültig löschen
python cli.py delete-emails-by-sender --label TRASH --sender "hacker@malicious.com"

# 4. (Optional) Block in Gmail UI
```

---

## ⚠️ Fehlerbehandlung

### Fehler: "Label nicht gefunden"
```
❌ Label 'NonExistent' nicht gefunden
```

**Lösung:**
```bash
python cli.py list-labels  # Finde gültige Label-Namen
```

### Fehler: "Keine E-Mails gefunden"
```
ℹ️  Keine E-Mails von 'xyz@domain.com' gefunden
```

**Gründe:**
- ✗ Falscher Label
- ✗ Falscher Absender
- ✗ E-Mails bereits gelöscht

**Lösung:**
```bash
# Prüfe mit filter-emails
python cli.py filter-emails --label INBOX --sender "xyz@domain.com"
```

### Rate Limit (zu viele API-Anfragen)
```
❌ Fehler: quotaExceeded
```

**Lösung:**
```bash
# Warte einige Sekunden und versuche erneut
sleep 60
python cli.py delete-emails-by-sender --label SPAM --sender "x" --confirm
```

---

## 📊 Performance

| Operation | Zeit | API-Calls |
|-----------|------|-----------|
| Filter (bis 500 E-Mails) | <2s | 2 |
| Löschen 100 E-Mails (Batch) | <3s | 10-15 |
| Löschen 500 E-Mails (Batch) | <5s | 50-75 |

**Tipp:** Batch-Operationen sind ~90% schneller als einzeln!

---

## ✅ Best Practices

1. **Immer Vorschau ansehen** bevor gelöscht wird
2. **Erst in Papierkorb** statt direkt löschen
3. **Nach 1 Woche** überprüfen, dann endgültig löschen
4. **Filter-Queries testen** mit `filter-emails` zuerst
5. **Cron-Jobs regelmäßig prüfen** (z.B. monatlich)

---

## 🔐 Sicherheit

### Datenschutz
- ✅ Nur deine Gmail API-Credentials (lokal)
- ✅ Keine Cloud-Speicherung
- ✅ Keine Weitergabe an Dritte

### Datenverlust verhindern
- ✅ Nutze `trash-emails-by-sender` statt direkt löschen
- ✅ Teste mit `filter-emails` zuerst
- ✅ 30 Tage im Papierkorb = Rettungsfenster

### Automation sichern
- ✅ Backup von Scripts machen
- ✅ Test in STAGING (z.B. mit Label "TEST")
- ✅ Dokumentation für alle Operationen

---

## 📞 Support

**Problem:** Delete funktioniert nicht
```bash
# 1. Überprüfe Syntax
python cli.py delete-emails-by-sender --help

# 2. Teste mit filter-emails
python cli.py filter-emails --label INBOX --sender "test@domain.com"

# 3. Lies Logs (falls aktiviert)
tail logs/*.log
```

**Problem:** Zu viele API-Calls
```bash
# Nutze Batch-Operationen!
# Statt 100 einzelne Calls = 1-2 Batch-Calls
```

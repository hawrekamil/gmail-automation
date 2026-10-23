"""Unit-Tests fuer den EmailService."""

from gmail_bot.models import EmailSummary, SendEmailRequest


def test_email_summary_from_api():
    data = {
        "id": "abc123",
        "thread_id": "thread1",
        "subject": "Test Betreff",
        "from": "sender@example.com",
        "to": "receiver@example.com",
        "date": "Mon, 1 Jan 2026 10:00:00 +0000",
        "snippet": "Hallo Welt",
        "label_ids": ["INBOX", "UNREAD"],
        "is_unread": True,
    }
    email = EmailSummary.from_api(data)
    assert email.id == "abc123"
    assert email.subject == "Test Betreff"
    assert email.is_unread is True


def test_send_email_request_validation():
    req = SendEmailRequest(to="", subject="Test", body="Hallo")
    try:
        req.validate()
        assert False, "Sollte ValueError werfen"
    except ValueError as e:
        assert "Empfaenger" in str(e)


def test_send_email_request_valid():
    req = SendEmailRequest(to="user@test.de", subject="Hi", body="Welt")
    req.validate()  # Kein Fehler erwartet

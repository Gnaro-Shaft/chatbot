"""Tests pour rgpd/consent.py."""

from unittest.mock import patch

from chatbot.rgpd.consent import CONSENT_TEXT, display_consent, get_consent


def test_display_consent_prints_text() -> None:
    """display_consent affiche le texte de consentement."""
    with patch("builtins.print") as mock_print:
        display_consent()
        mock_print.assert_called_once_with(CONSENT_TEXT)


@patch("builtins.input", return_value="o")
def test_get_consent_returns_true_for_oui(mock_input: object) -> None:
    """Consentiment "o" ou "oui" renvoie True."""
    assert get_consent() is True


@patch("builtins.input", return_value="n")
def test_get_consent_returns_false_for_non(mock_input: object) -> None:
    """Consentiment "n" renvoie False."""
    assert get_consent() is False


@patch("builtins.input", return_value="")
def test_get_consent_empty_input_is_consent(mock_input: object) -> None:
    """Entrée vide = consentement implicite par défaut."""
    assert get_consent() is True


def test_get_consent_eof_error_returns_false() -> None:
    """EOF (Ctrl+D) = pas de consentement => False."""
    with patch("builtins.input", side_effect=EOFError):
        assert get_consent() is False


def test_get_consent_keyboard_interrupt_returns_false() -> None:
    """Ctrl+C = pas de consentement => False."""
    with patch("builtins.input", side_effect=KeyboardInterrupt):
        assert get_consent() is False

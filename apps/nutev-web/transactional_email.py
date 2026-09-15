from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
import os
import smtplib
import ssl


@dataclass(frozen=True, slots=True)
class MailDeliveryResult:
    status: str
    detail: str = ""


def _setting(name: str) -> str:
    return str(os.environ.get(name) or "").strip()


def public_origin() -> str:
    configured = _setting("NUTEV_PUBLIC_ORIGIN")
    if configured:
        return configured.rstrip("/")
    domain = _setting("NUTEV_DOMAIN")
    return f"https://{domain}" if domain else ""


def email_configured() -> bool:
    return bool(_setting("NUTEV_SMTP_HOST") and _setting("NUTEV_SMTP_FROM"))


def _send(*, recipient: str, subject: str, text: str) -> MailDeliveryResult:
    host = _setting("NUTEV_SMTP_HOST")
    sender = _setting("NUTEV_SMTP_FROM")
    if not host or not sender:
        return MailDeliveryResult("not_configured")
    try:
        port = int(_setting("NUTEV_SMTP_PORT") or "587")
    except ValueError:
        return MailDeliveryResult("configuration_error", "invalid SMTP port")
    username = _setting("NUTEV_SMTP_USERNAME")
    password = str(os.environ.get("NUTEV_SMTP_PASSWORD") or "")
    use_starttls = (_setting("NUTEV_SMTP_STARTTLS") or "true").casefold() not in {"0", "false", "no"}

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(text)

    try:
        with smtplib.SMTP(host, port, timeout=15) as client:
            client.ehlo()
            if use_starttls:
                client.starttls(context=ssl.create_default_context())
                client.ehlo()
            if username:
                client.login(username, password)
            client.send_message(message)
    except Exception as exc:
        # Never include message content or tokens in this detail.
        return MailDeliveryResult("failed", type(exc).__name__)
    return MailDeliveryResult("sent")


def send_access_approved_email(*, recipient: str, display_name: str, invitation_url: str) -> MailDeliveryResult:
    if not invitation_url:
        return MailDeliveryResult("configuration_error", "public origin unavailable")
    text = (
        f"Olá, {display_name}.\n\n"
        "Seu acesso ao NutEV foi aprovado. Use o link temporário abaixo para criar sua senha:\n\n"
        f"{invitation_url}\n\n"
        "O link é de uso único e expira em 72 horas. Criar a conta não concede automaticamente "
        "acesso a projetos ou dados científicos privados.\n\n"
        "Se você não esperava esta mensagem, ignore-a.\n"
    )
    return _send(
        recipient=recipient,
        subject="Seu acesso ao NutEV foi aprovado",
        text=text,
    )


def send_password_reset_email(*, recipient: str, display_name: str, reset_url: str) -> MailDeliveryResult:
    if not reset_url:
        return MailDeliveryResult("configuration_error", "public origin unavailable")
    text = (
        f"Olá, {display_name}.\n\n"
        "Recebemos uma solicitação para redefinir sua senha do NutEV. Use o link abaixo:\n\n"
        f"{reset_url}\n\n"
        "O link é de uso único e expira em 1 hora. Ao definir a nova senha, todas as sessões "
        "ativas da conta serão encerradas.\n\n"
        "Se você não solicitou a redefinição, ignore esta mensagem.\n"
    )
    return _send(
        recipient=recipient,
        subject="Redefinição de senha — NutEV",
        text=text,
    )

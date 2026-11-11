import logging
import base64
import io
from email.utils import formataddr
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_credentials_email(user, password):
    subject = "Your Invitation & Login Details - Wangari's Birthday"
    site = getattr(settings, 'SITE_URL', '') or 'https://wangari.site'
    login_url = f"{site.rstrip('/')}/accounts/login/"
    context = {
        'user': user,
        'password': password,
        'login_url': login_url,
        'site_url': site.rstrip('/'),
        'name': user.real_name or user.username,
    }
    html_message = render_to_string('emails/credentials_email.html', context)
    plain_message = strip_tags(html_message)
    try:
        from_name = getattr(settings, 'DEFAULT_FROM_NAME', "Wangari's Birthday")
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '') or getattr(settings, 'EMAIL_HOST_USER', '') or 'noreply@wangari.site'
        from_header = formataddr((from_name, from_email))
        reply_to = [a for a in [getattr(settings, 'REPLY_TO_EMAIL', '') or getattr(settings, 'EMAIL_HOST_USER', '')] if a]
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=from_header,
            to=[user.email],
            reply_to=reply_to,
            headers={'X-Priority': '3'},
        )
        email.attach_alternative(html_message, 'text/html')
        email.send(fail_silently=False)
        logger.info(f"Credentials email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send credentials email to {user.email}: {e}")
        return False


def generate_ticket_qr_data_uri(user, request=None):
    """Return a data URI PNG QR code encoding the ticket verification URL."""
    try:
        import qrcode
    except Exception:
        return None
    try:
        ticket = user.ensure_ticket() if hasattr(user, 'ensure_ticket') else getattr(user, 'ticket_code', None)
        if not ticket:
            return None
        base = getattr(settings, 'SITE_URL', '') or 'https://wangari.site'
        if request is not None:
            try:
                base = request.build_absolute_uri('/').rstrip('/')
            except Exception:
                pass
        url = f"{base.rstrip('/')}/accounts/scan-ticket/{ticket}/"
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        return f"data:image/png;base64,{b64}", url
    except Exception as e:
        logger.error(f"Failed to generate QR for {getattr(user, 'email', user)}: {e}")
        return None

import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_credentials_email(user, password):
    subject = "Your Invitation & Login Details - Wangari's Birthday"
    login_url = f"{settings.SITE_URL.rstrip('/')}/accounts/login/" if getattr(settings, 'SITE_URL', '') else '/accounts/login/'
    context = {
        'user': user,
        'password': password,
        'login_url': login_url,
        'name': user.real_name or user.username,
    }
    html_message = render_to_string('emails/credentials_email.html', context)
    plain_message = strip_tags(html_message)
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@wangaribirthday.com'),
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Credentials email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send credentials email to {user.email}: {e}")
        return False

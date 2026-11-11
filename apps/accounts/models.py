import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
from .managers import UserManager


class OTPCode(models.Model):
    VERIFICATION = 'verification'
    PASSWORD_RESET = 'password_reset'
    OTP_TYPES = [
        (VERIFICATION, 'Email Verification'),
        (PASSWORD_RESET, 'Password Reset'),
    ]
    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=6, db_index=True)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.expires_at

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)


class PasswordResetToken(models.Model):
    email = models.EmailField(db_index=True)
    token = models.CharField(max_length=100, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.expires_at

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('SELLER', 'Admin/Organiser'),
        ('BUYER', 'Guest'),
    ]

    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='BUYER')
    created_by = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='created_buyers')
    real_name = models.CharField(max_length=150, blank=True, default='')
    email_verified = models.BooleanField(default=False)
    location = models.CharField(max_length=255, blank=True, default='')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    must_change_password = models.BooleanField(default=False)
    ticket_code = models.CharField(max_length=64, unique=True, null=True, blank=True, db_index=True)
    ticket_issued_at = models.DateTimeField(null=True, blank=True)
    has_paid = models.BooleanField(default=True)

    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.role})"

    def is_seller(self):
        return self.role == 'SELLER'

    def is_buyer(self):
        return self.role == 'BUYER'

    def ensure_ticket(self):
        if self.is_buyer() and not self.ticket_code:
            self.ticket_code = uuid.uuid4().hex
            if not self.ticket_issued_at:
                self.ticket_issued_at = timezone.now()
            self.save(update_fields=['ticket_code', 'ticket_issued_at'])
        return self.ticket_code

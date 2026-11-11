from django.db import models


class TicketType(models.Model):
    TICKET_CHOICES = [('REGULAR', 'Regular'), ('VIP', 'VIP')]
    name = models.CharField(max_length=20, choices=TICKET_CHOICES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.get_name_display()} Ticket — KSh {self.price}"


class Event(models.Model):
    title = models.CharField(max_length=200, default="Wangari's Birthday")
    venue = models.CharField(max_length=255, blank=True)
    event_date = models.DateTimeField(null=True, blank=True)
    schedule = models.TextField(blank=True, help_text="Schedule/agenda details")
    description = models.TextField(blank=True)
    additional_info = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class WishlistItem(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='wishlist/')
    description = models.TextField(blank=True)
    link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class OutfitIdea(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='outfits/')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

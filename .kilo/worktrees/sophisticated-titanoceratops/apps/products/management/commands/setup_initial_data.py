from django.core.management.base import BaseCommand
from apps.products.models import TicketType


class Command(BaseCommand):
    help = 'Create initial ticket types for Wangari\'s birthday'

    def handle(self, *args, **kwargs):
        TicketType.objects.get_or_create(
            name='REGULAR',
            defaults={'price': 500.00, 'description': 'Standard entry to the birthday celebration'}
        )
        TicketType.objects.get_or_create(
            name='VIP',
            defaults={'price': 1500.00, 'description': 'VIP entry with exclusive perks & front-row access'}
        )
        self.stdout.write(self.style.SUCCESS('Ticket types created successfully!'))

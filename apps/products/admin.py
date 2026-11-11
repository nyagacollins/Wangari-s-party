from django.contrib import admin
from .models import TicketType, Event, WishlistItem, OutfitIdea, ScheduleItem, Activity


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_available', 'created_at', 'updated_at')
    list_filter = ('is_available',)
    search_fields = ('name',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'venue', 'event_date', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'venue')


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title',)


@admin.register(OutfitIdea)
class OutfitIdeaAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title',)


@admin.register(ScheduleItem)
class ScheduleItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_time', 'end_time', 'location', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'location', 'description')
    ordering = ('order', 'start_time')
    list_editable = ('order', 'is_active')


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'time', 'location', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'location', 'description')
    ordering = ('time', '-created_at')
    list_editable = ('is_active',)

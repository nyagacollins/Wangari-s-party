from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'real_name', 'role', 'location', 'has_paid', 'ticket_code', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'has_paid', 'must_change_password', 'date_joined')
    search_fields = ('username', 'email', 'real_name', 'phone_number', 'location', 'ticket_code')

    fieldsets = UserAdmin.fieldsets + (
        ('Guest Info', {'fields': ('phone_number', 'role', 'created_by', 'real_name', 'location', 'latitude', 'longitude', 'must_change_password', 'ticket_code', 'ticket_issued_at', 'has_paid')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Guest Info', {'fields': ('phone_number', 'role', 'created_by', 'real_name', 'location', 'must_change_password', 'has_paid')}),
    )
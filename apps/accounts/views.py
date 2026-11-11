from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model

from .forms import CustomLoginForm, AdminCreateGuestForm, ForcePasswordChangeForm
from .decorators import seller_required
from .utils import send_credentials_email
from apps.products.models import Event, WishlistItem, OutfitIdea

User = get_user_model()


def login_view(request):
    if request.user.is_authenticated:
        if getattr(request.user, 'must_change_password', False) and request.user.is_buyer():
            return redirect('accounts:force_password_change')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        data = request.POST.copy()
        identifier = (data.get('username') or '').strip()
        if identifier and '@' in identifier:
            u = User.objects.filter(email__iexact=identifier).first()
            if u:
                data['username'] = u.get_username()
        form = CustomLoginForm(request, data=data)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if getattr(user, 'must_change_password', False) and user.is_buyer():
                return redirect('accounts:force_password_change')
            return redirect('accounts:dashboard')
    else:
        form = CustomLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def force_password_change(request):
    user = request.user
    if not getattr(user, 'must_change_password', False):
        return redirect('accounts:dashboard')
    if request.method == 'POST':
        form = ForcePasswordChangeForm(user, request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password1'])
            user.must_change_password = False
            user.save(update_fields=['password', 'must_change_password'])
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully. Welcome to your invitation!')
            return redirect('accounts:dashboard')
    else:
        form = ForcePasswordChangeForm(user)
    return render(request, 'accounts/force_password_change.html', {'form': form})


@login_required
def dashboard(request):
    user = request.user
    if getattr(user, 'must_change_password', False) and user.is_buyer():
        return redirect('accounts:force_password_change')

    if user.is_seller():
        total_guests = User.objects.filter(role='BUYER').count()
        recent_guests = User.objects.filter(role='BUYER').order_by('-date_joined')[:10]
        return render(request, 'accounts/seller_dashboard.html', {
            'total_guests': total_guests,
            'recent_guests': recent_guests,
        })

    event = Event.objects.filter(is_active=True).order_by('-updated_at').first()
    wishlist = WishlistItem.objects.filter(is_active=True).order_by('-created_at')
    outfits = OutfitIdea.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'accounts/buyer_dashboard.html', {
        'event': event,
        'wishlist_items': wishlist,
        'outfit_ideas': outfits,
    })


@login_required
@seller_required
def register_buyer(request):
    if request.method == 'POST':
        form = AdminCreateGuestForm(request.POST)
        if form.is_valid():
            guest = form.save(created_by=request.user)
            temp = getattr(guest, '_temp_password', '')
            if send_credentials_email(guest, temp):
                messages.success(request, f"Guest '{guest.real_name or guest.username}' created and credentials emailed to {guest.email}.")
            else:
                messages.warning(request, f"Guest created but email could not be sent. Share credentials manually — username: {guest.username}, temporary password: {temp}")
            return redirect('accounts:manage_buyers')
    else:
        form = AdminCreateGuestForm()
    return render(request, 'accounts/register_buyer.html', {'form': form})


@login_required
@seller_required
def manage_buyers(request):
    buyers = User.objects.filter(role='BUYER').order_by('-date_joined')
    return render(request, 'accounts/manage_buyers.html', {'buyers': buyers})


@login_required
@seller_required
def toggle_buyer_status(request, buyer_id):
    buyer = get_object_or_404(User, id=buyer_id, role='BUYER')
    buyer.is_active = not buyer.is_active
    buyer.save(update_fields=['is_active'])
    status = 'activated' if buyer.is_active else 'deactivated'
    messages.success(request, f'Guest {buyer.username} has been {status}.')
    return redirect('accounts:manage_buyers')


@login_required
@seller_required
def delete_buyer(request, buyer_id):
    buyer = get_object_or_404(User, id=buyer_id, role='BUYER')
    if request.method == 'POST':
        name = buyer.real_name or buyer.username or buyer.email
        buyer.delete()
        messages.success(request, f"Guest '{name}' has been deleted.")
    return redirect('accounts:manage_buyers')

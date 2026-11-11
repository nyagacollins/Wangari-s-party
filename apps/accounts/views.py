import json
from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST

from .forms import CustomLoginForm, AdminCreateGuestForm, ForcePasswordChangeForm
from .decorators import seller_required
from .utils import send_credentials_email, generate_ticket_qr_data_uri
from apps.products.models import Event, WishlistItem, OutfitIdea, ScheduleItem, Activity

User = get_user_model()

DEFAULT_WISHLIST = [
    {'title': 'Perfume / Fragrance', 'description': 'A lovely scent to make the day special.', 'link': '', 'emoji': '🌸', 'image': '', 'image_url': ''},
    {'title': 'Handbag / Purse', 'description': 'A classy bag for everyday outings.', 'link': '', 'emoji': '👜', 'image': '', 'image_url': ''},
    {'title': 'Jewelry', 'description': 'Necklace, bracelet, or earrings.', 'link': '', 'emoji': '💎', 'image': '', 'image_url': ''},
    {'title': 'Skincare Set', 'description': 'Self-care and glow essentials.', 'link': '', 'emoji': '✨', 'image': '', 'image_url': ''},
    {'title': 'Flowers & Card', 'description': 'A heartfelt note with fresh flowers.', 'link': '', 'emoji': '💐', 'image': '', 'image_url': ''},
    {'title': 'Gift Voucher', 'description': 'Let Wangari pick something she loves.', 'link': '', 'emoji': '🎁', 'image': '', 'image_url': ''},
]

DEFAULT_OUTFITS = [
    {'title': 'Outfit idea 1', 'description': 'Elegant and celebratory.', 'emoji': '👗', 'image': '', 'image_url': ''},
    {'title': 'Outfit idea 2', 'description': 'Smart and stylish.', 'emoji': '👔', 'image': '', 'image_url': ''},
    {'title': 'Outfit idea 3', 'description': 'Comfortable and chic.', 'emoji': '👠', 'image': '', 'image_url': ''},
    {'title': 'Outfit idea 4', 'description': 'Add your inspiration.', 'emoji': '✨', 'image': '', 'image_url': ''},
]


def _load_static_items(json_rel_path, default_items, static_subdir, default_title):
    config_path = Path(settings.BASE_DIR) / json_rel_path
    items = default_items
    try:
        if config_path.exists():
            with config_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                items = data
    except Exception:
        items = default_items

    normalized = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        item = {
            'title': (raw.get('title') or '').strip() or default_title,
            'description': (raw.get('description') or '').strip(),
            'link': (raw.get('link') or '').strip(),
            'emoji': (raw.get('emoji') or '✨').strip() or '✨',
            'image': (raw.get('image') or '').strip(),
            'image_url': (raw.get('image_url') or raw.get('url') or '').strip(),
            'display_src': '',
        }
        if item['image'].lower().startswith(('http://', 'https://')):
            item['image_url'] = item['image_url'] or item['image']
            item['image'] = ''
        if item['image_url']:
            item['display_src'] = item['image_url']
        elif item['image']:
            name = item['image'].lstrip('/\\')
            if name.lower().startswith('static/'):
                name = name[7:].lstrip('/\\')
            if '/' in name or '\\' in name:
                item['display_src'] = f"/static/{name.replace('\\', '/')}"
            else:
                item['display_src'] = f"/static/{static_subdir}/{name}"
        normalized.append(item)
    return normalized or default_items


def load_hardcoded_wishlist():
    """Load wishlist from static/images/wishlist/items.json for easy editing."""
    return _load_static_items('static/images/wishlist/items.json', DEFAULT_WISHLIST, 'images/wishlist', 'Wishlist Item')


def load_hardcoded_outfits():
    """Load outfit ideas from static/images/outfits/items.json for easy editing."""
    return _load_static_items('static/images/outfits/items.json', DEFAULT_OUTFITS, 'images/outfits', 'Outfit Idea')


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
        schedules = ScheduleItem.objects.filter(is_active=True).order_by('order', 'start_time')[:10]
        activities = Activity.objects.filter(is_active=True).order_by('time', '-created_at')[:10]
        return render(request, 'accounts/seller_dashboard.html', {
            'total_guests': total_guests,
            'recent_guests': recent_guests,
            'schedule_items': schedules,
            'activities': activities,
        })

    event = Event.objects.filter(is_active=True).order_by('-updated_at').first()
    schedules = ScheduleItem.objects.filter(is_active=True).order_by('order', 'start_time')
    activities = Activity.objects.filter(is_active=True).order_by('time', '-created_at')
    user.ensure_ticket()
    qr_data = generate_ticket_qr_data_uri(user, request=request)
    qr_image = qr_data[0] if qr_data else None
    ticket_url = qr_data[1] if qr_data else None
    return render(request, 'accounts/buyer_dashboard.html', {
        'event': event,
        'wishlist_items': load_hardcoded_wishlist(),
        'outfit_ideas': load_hardcoded_outfits(),
        'schedule_items': schedules,
        'activities': activities,
        'qr_image': qr_image,
        'ticket_url': ticket_url,
    })


@login_required
@require_POST
def update_my_location(request):
    user = request.user
    if not user.is_buyer():
        return HttpResponseForbidden('Only guests can update location.')
    try:
        data = json.loads(request.body.decode('utf-8')) if request.content_type and 'application/json' in request.content_type else request.POST
    except Exception:
        data = request.POST
    lat = data.get('latitude') or data.get('lat')
    lng = data.get('longitude') or data.get('lng')
    label = (data.get('label') or data.get('location') or '').strip()
    updated = []
    try:
        if lat not in (None, '') and lng not in (None, ''):
            user.latitude = float(lat)
            user.longitude = float(lng)
            updated += ['latitude', 'longitude']
            if not label:
                label = f"{user.latitude:.5f}, {user.longitude:.5f}"
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Invalid coordinates.'}, status=400)
    if label:
        user.location = label[:255]
        updated.append('location')
    if updated:
        user.save(update_fields=list(dict.fromkeys(updated)))
    return JsonResponse({'ok': True, 'location': user.location, 'latitude': user.latitude, 'longitude': user.longitude})


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
    schedules = ScheduleItem.objects.order_by('order', 'start_time')
    activities = Activity.objects.order_by('time', '-created_at')
    return render(request, 'accounts/manage_buyers.html', {
        'buyers': buyers,
        'schedule_items': schedules,
        'activities': activities,
    })


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


@login_required
@seller_required
def scan_ticket(request, ticket_code):
    guest = get_object_or_404(User, ticket_code=ticket_code, role='BUYER')
    return render(request, 'accounts/scan_ticket.html', {'guest': guest})

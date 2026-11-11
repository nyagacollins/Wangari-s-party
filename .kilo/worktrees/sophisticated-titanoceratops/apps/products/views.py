from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import seller_required, buyer_required
from .models import TicketType
from .forms import TicketPriceForm, TicketSelectionForm


@login_required
@seller_required
def manage_products(request):
    tickets = TicketType.objects.all()
    return render(request, 'products/manage_products.html', {'products': tickets})


@login_required
@seller_required
def update_product_price(request, product_id):
    ticket = get_object_or_404(TicketType, id=product_id)

    if request.method == 'POST':
        form = TicketPriceForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, f'{ticket.get_name_display()} ticket price updated!')
            return redirect('products:manage_products')
    else:
        form = TicketPriceForm(instance=ticket)

    return render(request, 'products/update_price.html', {'form': form, 'product': ticket})


@login_required
@buyer_required
def select_snacks(request):
    try:
        regular = TicketType.objects.get(name='REGULAR')
        vip = TicketType.objects.get(name='VIP')
    except TicketType.DoesNotExist:
        messages.error(request, 'Ticket types not found. Please contact the organiser.')
        return redirect('accounts:dashboard')

    total_amount = 0

    if request.method == 'POST':
        form = TicketSelectionForm(request.POST)
        if form.is_valid():
            regular_qty = form.cleaned_data['regular_quantity']
            vip_qty = form.cleaned_data['vip_quantity']

            if regular_qty == 0 and vip_qty == 0:
                messages.warning(request, 'Please select at least one ticket.')
            else:
                total_amount = (regular_qty * regular.price) + (vip_qty * vip.price)

                request.session['order_data'] = {
                    'regular_quantity': regular_qty,
                    'vip_quantity': vip_qty,
                    'regular_price': float(regular.price),
                    'vip_price': float(vip.price),
                    'total_amount': float(total_amount),
                }

                return redirect('payments:payment_form')
    else:
        form = TicketSelectionForm()

    context = {
        'form': form,
        'regular': regular,
        'vip': vip,
        'total_amount': total_amount,
    }

    return render(request, 'products/select_snacks.html', context)

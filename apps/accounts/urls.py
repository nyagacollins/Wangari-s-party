from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.force_password_change, name='force_password_change'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register-buyer/', views.register_buyer, name='register_buyer'),
    path('manage-buyers/', views.manage_buyers, name='manage_buyers'),
    path('toggle-buyer-status/<int:buyer_id>/', views.toggle_buyer_status, name='toggle_buyer_status'),
]

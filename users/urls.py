from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    path('profile/delete/', views.delete_account_view, name='delete_account'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/approve-institution/<int:institution_id>/', views.approve_institution_view, name='approve_institution'),
    path('admin-dashboard/reject-institution/<int:institution_id>/', views.reject_institution_view, name='reject_institution'),
    path('admin-dashboard/revoke-institution/<int:institution_id>/', views.revoke_institution_approval_view, name='revoke_institution'),
    path('institution-settings/', views.institution_settings_view, name='institution_settings'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service_view, name='terms_of_service'),
    path('cookie-policy/', views.cookie_policy_view, name='cookie_policy'),
]

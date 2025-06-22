# wallets/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.wallet_home, name='wallet_home'),
    path('credential/<uuid:credential_id>/', views.credential_detail, name='credential_detail'),
    path('credential/<uuid:credential_id>/share/', views.share_credential, name='share_credential'),
    path('credential/<uuid:credential_id>/archive/', views.archive_credential, name='archive_credential'),
    path('credential/<uuid:credential_id>/unarchive/', views.unarchive_credential, name='unarchive_credential'),
    path('credential/<uuid:credential_id>/download/', views.download_credential, name='download_credential'),
    path('shared/<uuid:credential_id>/', views.view_shared_credential, name='view_shared_credential'),
]
# This file defines the URL patterns for the wallets app, mapping URLs to views.
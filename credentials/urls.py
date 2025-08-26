# credentials/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('schemas/', views.schema_list, name='schema_list'),
    path('schemas/create/', views.schema_create, name='schema_create'),
    path('issue/', views.issue_credential, name='issue_credential'),
    path('issue/<uuid:schema_id>/', views.issue_credential, name='issue_credential_with_schema'),
    path('issued/', views.issued_credentials, name='issued_credentials'),
    path('credential/<uuid:credential_id>/', views.credential_detail, name='credential_detail'),
    path('credential/<uuid:credential_id>/edit/', views.edit_credential, name='edit_credential'),
    path('credential/<uuid:credential_id>/revoke/', views.revoke_credential, name='revoke_credential'),
    path('verify/', views.verify_credential, name='verify_credential'),
]

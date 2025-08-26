from django.contrib import admin
from .models import CredentialSchema, Credential

@admin.register(CredentialSchema)
class CredentialSchemaAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'version', 'created_by', 'created_at', 'updated_at')
    list_filter = ('type', 'created_at', 'updated_at')
    search_fields = ('name', 'created_by__username', 'created_by__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'type', 'version', 'fields')
        }),
        ('Creator', {
            'fields': ('created_by',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    list_display = ('title', 'credential_type', 'issuer', 'holder', 'status', 'created_at', 'issued_at')
    list_filter = ('status', 'credential_type', 'created_at', 'issued_at', 'expiration_date')
    search_fields = ('title', 'description', 'issuer__username', 'holder__username', 'issuer__email', 'holder__email')
    readonly_fields = ('id', 'created_at', 'issued_at', 'vc_hash')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'credential_type', 'schema')
        }),
        ('Parties', {
            'fields': ('issuer', 'holder')
        }),
        ('Status & Dates', {
            'fields': ('status', 'created_at', 'issued_at', 'expiration_date')
        }),
        ('Revocation', {
            'fields': ('revocation_reason',),
            'classes': ('collapse',)
        }),
        ('Technical Details', {
            'fields': ('vc_json', 'vc_hash'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('issuer', 'holder', 'schema')

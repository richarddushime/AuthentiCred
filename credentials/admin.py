from django.contrib import admin
from .models import CredentialSchema, Credential, VerificationRecord

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
    search_fields = ('title', 'description', 'issuer__username', 'holder__username', 'issuer__email', 'holder__email', 'vc_hash')
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

@admin.register(VerificationRecord)
class VerificationRecordAdmin(admin.ModelAdmin):
    list_display = ('verifier', 'credential_hash', 'verification_date', 'is_valid', 'source')
    list_filter = ('is_valid', 'source', 'verification_date')
    search_fields = ('verifier__username', 'verifier__email', 'credential_hash')
    readonly_fields = ('id', 'verification_date')
    ordering = ('-verification_date',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('verifier', 'credential_hash', 'credential')
        }),
        ('Verification Details', {
            'fields': ('is_valid', 'source', 'verification_details')
        }),
        ('Timestamps', {
            'fields': ('verification_date',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('verifier', 'credential')

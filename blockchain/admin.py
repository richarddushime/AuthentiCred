from django.contrib import admin
from .models import OnChainTransaction, DIDRegistration

@admin.register(OnChainTransaction)
class OnChainTransactionAdmin(admin.ModelAdmin):
    list_display = ('tx_hash', 'transaction_type', 'status', 'block_number', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at', 'updated_at')
    search_fields = ('tx_hash', 'metadata')
    readonly_fields = ('tx_hash', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('tx_hash', 'transaction_type', 'status')
        }),
        ('Blockchain Information', {
            'fields': ('block_number', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request)

@admin.register(DIDRegistration)
class DIDRegistrationAdmin(admin.ModelAdmin):
    list_display = ('did', 'institution', 'registered_at', 'trust_updated')
    list_filter = ('trust_updated', 'registered_at')
    search_fields = ('did', 'institution__name', 'institution__user__username')
    readonly_fields = ('did', 'registered_at')
    ordering = ('-registered_at',)
    
    fieldsets = (
        ('DID Information', {
            'fields': ('did', 'public_key')
        }),
        ('Institution', {
            'fields': ('institution',)
        }),
        ('Blockchain Transaction', {
            'fields': ('transaction',)
        }),
        ('Status', {
            'fields': ('trust_updated',)
        }),
        ('Timestamps', {
            'fields': ('registered_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('institution__user', 'transaction')

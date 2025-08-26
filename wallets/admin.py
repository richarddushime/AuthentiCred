from django.contrib import admin
from .models import Wallet, WalletCredential

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name')
        }),
        ('Security', {
            'fields': ('private_key',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(WalletCredential)
class WalletCredentialAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'credential', 'added_at', 'is_archived')
    list_filter = ('is_archived', 'added_at')
    search_fields = ('wallet__user__username', 'credential__title', 'credential__credential_type')
    readonly_fields = ('id', 'added_at')
    ordering = ('-added_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('wallet', 'credential')
        }),
        ('Status', {
            'fields': ('is_archived',)
        }),
        ('Timestamps', {
            'fields': ('added_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('wallet__user', 'credential')

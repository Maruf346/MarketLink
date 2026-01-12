from django.contrib import admin
from .models import PaymentTransaction, PaymentEvent


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'order_id', 'amount', 'status', 'created_at', 'payment_date')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('transaction_id', 'bank_transaction_id', 'order__order_id')
    readonly_fields = ('created_at', 'updated_at', 'response_data_preview')
    list_per_page = 20
    
    fieldsets = (
        ('Transaction Info', {
            'fields': ('transaction_id', 'bank_transaction_id', 'order')
        }),
        ('Payment Details', {
            'fields': ('amount', 'currency', 'status', 'payment_date')
        }),
        ('Response Data', {
            'fields': ('response_data_preview',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_id(self, obj):
        return obj.order.order_id
    order_id.short_description = 'Order ID'
    
    def response_data_preview(self, obj):
        import json
        return json.dumps(obj.response_data, indent=2)
    response_data_preview.short_description = 'Response Data'


@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    list_display = ('event_id', 'order_id', 'status', 'processed', 'created_at')
    list_filter = ('status', 'processed', 'created_at')
    search_fields = ('event_id', 'order__order_id')
    readonly_fields = ('created_at', 'processed_at', 'payload_preview')
    list_per_page = 20
    
    def order_id(self, obj):
        return obj.order.order_id
    order_id.short_description = 'Order ID'
    
    def payload_preview(self, obj):
        import json
        return json.dumps(obj.payload, indent=2)
    payload_preview.short_description = 'Webhook Payload'
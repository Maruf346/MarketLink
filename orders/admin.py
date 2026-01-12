from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import RepairOrder


@admin.register(RepairOrder)
class RepairOrderAdmin(admin.ModelAdmin):
    list_display = ('order_id_short', 'customer_email', 'vendor_name', 'variant_name', 
                    'status_badge', 'total_amount_display', 'created_at', 'payment_status')
    list_filter = ('status', 'created_at', 'vendor__business_name', 'variant__service__name')
    search_fields = ('order_id', 'customer__email', 'vendor__business_name', 
                     'variant__name', 'payment_event_id')
    readonly_fields = ('order_id', 'created_at', 'updated_at', 'customer_email', 
                      'vendor_name', 'variant_name', 'payment_status', 'duration')
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['mark_as_completed', 'mark_as_cancelled']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'customer', 'vendor', 'variant', 'total_amount')
        }),
        ('Status & Payment', {
            'fields': ('status', 'payment_event_id', 'payment_status')
        }),
        ('Additional Info', {
            'fields': ('duration',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_id_short(self, obj):
        """Display shortened order ID"""
        return str(obj.order_id)[:8] + '...'
    order_id_short.short_description = 'Order ID'
    order_id_short.admin_order_field = 'order_id'
    
    def customer_email(self, obj):
        return obj.customer.email
    customer_email.short_description = 'Customer'
    customer_email.admin_order_field = 'customer__email'
    
    def vendor_name(self, obj):
        return obj.vendor.business_name
    vendor_name.short_description = 'Vendor'
    vendor_name.admin_order_field = 'vendor__business_name'
    
    def variant_name(self, obj):
        return f"{obj.variant.service.name} - {obj.variant.name}"
    variant_name.short_description = 'Service Variant'
    
    def status_badge(self, obj):
        """Display status with color-coded badge"""
        colors = {
            'pending': 'gray',
            'paid': 'blue',
            'processing': 'orange',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'black',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def total_amount_display(self, obj):
        return f"${obj.total_amount}"
    total_amount_display.short_description = 'Amount'
    total_amount_display.admin_order_field = 'total_amount'
    
    def payment_status(self, obj):
        """Display payment status indicator"""
        if obj.payment_event_id:
            return format_html(
                '<span style="color: green;">✓ Paid</span>'
            )
        elif obj.status == 'paid':
            return format_html(
                '<span style="color: green;">✓ Paid (via status)</span>'
            )
        else:
            return format_html(
                '<span style="color: orange;">● Pending</span>'
            )
    payment_status.short_description = 'Payment'
    
    def duration(self, obj):
        """Calculate time since order was created"""
        if obj.created_at:
            delta = timezone.now() - obj.created_at
            hours = delta.total_seconds() / 3600
            if hours < 1:
                return "Just now"
            elif hours < 24:
                return f"{int(hours)} hours ago"
            else:
                days = int(hours / 24)
                return f"{days} days ago"
        return "N/A"
    duration.short_description = 'Age'
    
    def mark_as_completed(self, request, queryset):
        """Admin action to mark orders as completed"""
        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} order(s) marked as completed.")
    mark_as_completed.short_description = "Mark selected orders as completed"
    
    def mark_as_cancelled(self, request, queryset):
        """Admin action to mark orders as cancelled"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"{updated} order(s) marked as cancelled.")
    mark_as_cancelled.short_description = "Mark selected orders as cancelled"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'customer', 
            'vendor', 
            'variant',
            'variant__service'
        )
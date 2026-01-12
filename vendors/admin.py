from django.contrib import admin
from django.utils.html import format_html
from .models import VendorProfile, Service, ServiceVariant


class ServiceVariantInline(admin.TabularInline):
    """Inline editing for Service Variants"""
    model = ServiceVariant
    extra = 1
    fields = ('name', 'price', 'estimated_minutes', 'stock', 'is_active')
    ordering = ('price',)


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user_email', 'is_active', 'created_at', 'orders_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('business_name', 'user__email', 'address')
    readonly_fields = ('created_at', 'updated_at', 'user_email')
    list_per_page = 20
    
    fieldsets = (
        ('Vendor Information', {
            'fields': ('user', 'business_name', 'address')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Vendor Email'
    
    def orders_count(self, obj):
        count = obj.orders.count()
        return format_html(
            '<a href="/admin/orders/repairorder/?vendor__id={}" target="_blank">{}</a>',
            obj.id,
            count
        )
    orders_count.short_description = 'Total Orders'


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor_name', 'is_active', 'variants_count', 'created_at')
    list_filter = ('is_active', 'vendor__business_name', 'created_at')
    search_fields = ('name', 'description', 'vendor__business_name')
    readonly_fields = ('created_at', 'updated_at', 'vendor_name')
    list_per_page = 20
    inlines = [ServiceVariantInline]
    
    fieldsets = (
        ('Service Information', {
            'fields': ('vendor', 'name', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def vendor_name(self, obj):
        return obj.vendor.business_name
    vendor_name.short_description = 'Vendor'
    
    def variants_count(self, obj):
        count = obj.variants.count()
        return format_html(
            '<span class="badge">{}</span>',
            count
        )
    variants_count.short_description = 'Variants'


@admin.register(ServiceVariant)
class ServiceVariantAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_name', 'price', 'estimated_minutes', 'stock', 'is_active', 'orders_count')
    list_filter = ('is_active', 'service__vendor__business_name', 'service__name')
    search_fields = ('name', 'service__name', 'service__vendor__business_name')
    readonly_fields = ('created_at', 'updated_at', 'service_name', 'orders_count_display')
    list_per_page = 20
    
    fieldsets = (
        ('Variant Information', {
            'fields': ('service', 'name', 'price', 'estimated_minutes')
        }),
        ('Inventory', {
            'fields': ('stock',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('orders_count_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def service_name(self, obj):
        return obj.service.name
    service_name.short_description = 'Service'
    
    def orders_count(self, obj):
        return obj.orders.count()
    orders_count.short_description = 'Orders'
    
    def orders_count_display(self, obj):
        count = obj.orders.count()
        return format_html(
            '<a href="/admin/orders/repairorder/?variant__id={}" target="_blank">{}</a>',
            obj.id,
            count
        )
    orders_count_display.short_description = 'Total Orders'
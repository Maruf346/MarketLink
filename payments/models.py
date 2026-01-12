from django.db import models
from orders.models import RepairOrder
from django.utils import timezone

class PaymentTransaction(models.Model):
    """Track payment transactions"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    # SSLCommerz fields
    transaction_id = models.CharField(max_length=255, unique=True)
    bank_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Order reference
    order = models.ForeignKey(
        RepairOrder,
        on_delete=models.CASCADE,
        related_name='payment_transactions'
    )
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='BDT')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # SSLCommerz response data
    response_data = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"
    
    def mark_as_success(self, bank_transaction_id, response_data):
        """Mark payment as successful"""
        self.status = 'success'
        self.bank_transaction_id = bank_transaction_id
        self.response_data = response_data
        self.payment_date = timezone.now()
        self.save()
        
        # Update order status
        self.order.status = 'paid'
        self.order.save()


class PaymentEvent(models.Model):
    """For webhook idempotency"""
    
    event_id = models.CharField(max_length=255, unique=True)
    payment_transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.CASCADE,
        related_name='events',
        null=True,
        blank=True
    )
    order = models.ForeignKey(
        RepairOrder,
        on_delete=models.CASCADE,
        related_name='payment_events'
    )
    payload = models.JSONField()
    status = models.CharField(max_length=50, default='pending')
    processed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"PaymentEvent {self.event_id}"
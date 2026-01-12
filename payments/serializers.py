from rest_framework import serializers
from .models import PaymentTransaction, PaymentEvent


class PaymentTransactionSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source='order.order_id', read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'transaction_id', 'order_id', 'amount', 
            'currency', 'status', 'created_at', 'payment_date'
        ]
        read_only_fields = fields


class SSLCommerzWebhookSerializer(serializers.Serializer):
    """
    Serializer for SSLCommerz IPN/Webhook data
    Reference: https://developer.sslcommerz.com/doc/v4/#ipn
    """
    
    # Required fields
    tran_id = serializers.CharField()
    val_id = serializers.CharField()  # Validation ID for verification
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    status = serializers.CharField()
    
    # Order reference
    value_a = serializers.CharField()  # Order ID
    value_b = serializers.CharField()  # Customer ID
    value_c = serializers.CharField(required=False)  # Custom field
    value_d = serializers.CharField(required=False)  # Custom field
    
    # Customer info
    cus_name = serializers.CharField(required=False)
    cus_email = serializers.CharField(required=False)
    cus_phone = serializers.CharField(required=False)
    
    # Bank info
    bank_tran_id = serializers.CharField(required=False)
    card_type = serializers.CharField(required=False)
    card_no = serializers.CharField(required=False)
    card_issuer = serializers.CharField(required=False)
    card_brand = serializers.CharField(required=False)
    
    # Timestamps
    tran_date = serializers.CharField(required=False)
    
    def validate(self, data):
        """Additional validation"""
        status = data.get('status')
        
        # Check if status is valid
        valid_statuses = ['VALID', 'VALIDATED', 'FAILED', 'CANCELLED']
        if status not in valid_statuses:
            raise serializers.ValidationError({
                'status': f'Invalid payment status: {status}'
            })
        
        return data
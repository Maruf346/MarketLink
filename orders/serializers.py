from rest_framework import serializers
from .models import RepairOrder
from vendors.serializers import ServiceVariantSerializer
from core.serializers import UserSerializer


class RepairOrderSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    variant = ServiceVariantSerializer(read_only=True)
    
    class Meta:
        model = RepairOrder
        fields = [
            'order_id', 'customer', 'vendor', 'variant', 'status',
            'total_amount', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_id', 'customer', 'vendor', 'created_at', 'updated_at']


class CreateOrderSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField(required=True)
    
    def validate_variant_id(self, value):
        from vendors.models import ServiceVariant
        
        try:
            variant = ServiceVariant.objects.get(id=value, is_active=True)
            if variant.stock <= 0:
                raise serializers.ValidationError("This variant is out of stock")
        except ServiceVariant.DoesNotExist:
            raise serializers.ValidationError("Service variant not found")
        
        return value
    
    def create(self, validated_data):
        from vendors.models import ServiceVariant
        from .models import RepairOrder
        
        request = self.context.get('request')
        variant_id = validated_data['variant_id']
        
        # Get variant with lock (for concurrency)
        variant = ServiceVariant.objects.select_for_update().get(id=variant_id)
        
        # Check stock
        if variant.stock <= 0:
            raise serializers.ValidationError({"variant": "Out of stock"})
        
        # Decrement stock
        variant.stock -= 1
        variant.save()
        
        # Create order
        order = RepairOrder.objects.create(
            customer=request.user,
            vendor=variant.service.vendor,
            variant=variant,
            total_amount=variant.price,
            status='pending'
        )
        
        return order
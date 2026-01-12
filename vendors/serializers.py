from rest_framework import serializers
from .models import VendorProfile, Service, ServiceVariant
from core.serializers import UserSerializer


class VendorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = VendorProfile
        fields = ['id', 'user', 'business_name', 'address', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ServiceVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceVariant
        fields = ['id', 'name', 'price', 'estimated_minutes', 'stock', 'is_active']
        read_only_fields = ['id']


class ServiceSerializer(serializers.ModelSerializer):
    vendor = VendorProfileSerializer(read_only=True)
    variants = ServiceVariantSerializer(many=True, read_only=True)
    
    class Meta:
        model = Service
        fields = ['id', 'vendor', 'name', 'description', 'is_active', 'variants', 'created_at']
        read_only_fields = ['id', 'created_at']


class CreateServiceSerializer(serializers.ModelSerializer):
    variants = ServiceVariantSerializer(many=True, required=False)
    
    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'variants']
    
    def create(self, validated_data):
        variants_data = validated_data.pop('variants', [])
        service = Service.objects.create(**validated_data)
        
        for variant_data in variants_data:
            ServiceVariant.objects.create(service=service, **variant_data)
        
        return service
# orders/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
import redis
import json
from .models import RepairOrder
from .serializers import RepairOrderSerializer, CreateOrderSerializer
from core.permissions import IsCustomerUser


class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCustomerUser]
    
    def post(self, request):
        serializer = CreateOrderSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Redis lock for concurrency (simplified version)
        variant_id = serializer.validated_data['variant_id']
        redis_client = redis.Redis()
        lock_key = f"lock:variant:{variant_id}"
        
        try:
            # Try to acquire lock
            lock_acquired = redis_client.setnx(lock_key, "locked")
            if not lock_acquired:
                return Response(
                    {"error": "Service is currently being booked. Please try again."},
                    status=status.HTTP_409_CONFLICT
                )
            
            # Set lock expiration (10 seconds)
            redis_client.expire(lock_key, 10)
            
            # Create order within transaction
            with transaction.atomic():
                order = serializer.save()
            
            # Generate payment URL (mock for now)
            payment_url = f"/mock-payment/{order.order_id}/"
            
            return Response({
                'order': RepairOrderSerializer(order).data,
                'payment_url': payment_url,
                'message': 'Order created successfully. Proceed to payment.'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        finally:
            # Release lock
            redis_client.delete(lock_key)


class CustomerOrdersView(generics.ListAPIView):
    serializer_class = RepairOrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomerUser]
    
    def get_queryset(self):
        return RepairOrder.objects.filter(customer=self.request.user)


class VendorOrdersView(generics.ListAPIView):
    serializer_class = RepairOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if hasattr(self.request.user, 'vendor_profile'):
            return RepairOrder.objects.filter(vendor=self.request.user.vendor_profile)
        return RepairOrder.objects.none()
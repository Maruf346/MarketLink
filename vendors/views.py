from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from .serializers import *
from core.permissions import IsVendorUser


class VendorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendorUser]
    
    def get_object(self):
        return self.request.user.vendor_profile


class VendorServicesView(generics.ListCreateAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendorUser]
    
    def get_queryset(self):
        return Service.objects.filter(vendor=self.request.user.vendor_profile)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateServiceSerializer
        return ServiceSerializer
    
    def perform_create(self, serializer):
        serializer.save(vendor=self.request.user.vendor_profile)


class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendorUser]
    
    def get_queryset(self):
        return Service.objects.filter(vendor=self.request.user.vendor_profile)


class PublicServicesView(generics.ListAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Service.objects.filter(is_active=True)
        vendor_id = self.request.query_params.get('vendor')
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)
        return queryset
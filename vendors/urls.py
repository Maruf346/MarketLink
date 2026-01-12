# vendors/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.VendorProfileView.as_view(), name='vendor-profile'),
    path('services/', views.VendorServicesView.as_view(), name='vendor-services'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service-detail'),
    path('public/services/', views.PublicServicesView.as_view(), name='public-services'),
]
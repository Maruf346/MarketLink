# orders/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.CreateOrderView.as_view(), name='create-order'),
    path('my-orders/', views.CustomerOrdersView.as_view(), name='customer-orders'),
    path('vendor-orders/', views.VendorOrdersView.as_view(), name='vendor-orders'),
]
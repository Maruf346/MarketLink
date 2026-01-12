from django.urls import path
from . import views

urlpatterns = [
    # Payment initiation
    path('initiate/<uuid:order_id>/', views.InitiatePaymentView.as_view(), name='initiate-payment'),
    
    # SSLCommerz webhook (IPN)
    path('webhook/', views.PaymentWebhookView.as_view(), name='payment-webhook'),
    
    # Redirect URLs (for SSLCommerz)
    path('success/', views.PaymentSuccessView.as_view(), name='payment-success'),
    path('fail/', views.PaymentFailView.as_view(), name='payment-fail'),
    path('cancel/', views.PaymentCancelView.as_view(), name='payment-cancel'),
    
    # Payment status checking
    path('status/<uuid:order_id>/', views.PaymentStatusView.as_view(), name='payment-status'),
    path('history/', views.PaymentHistoryView.as_view(), name='payment-history'),
]
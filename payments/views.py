from django.shortcuts import redirect
from rest_framework import status, views, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import transaction
import logging
from urllib.parse import urljoin
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.db import models
from rest_framework.permissions import IsAuthenticated, AllowAny
from orders.models import RepairOrder
from .models import PaymentTransaction, PaymentEvent
from .serializers import SSLCommerzWebhookSerializer, PaymentTransactionSerializer
from .services import get_payment_gateway

logger = logging.getLogger(__name__)


class InitiatePaymentView(views.APIView):
    """Initiate payment for an order"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, order_id):
        try:
            order = RepairOrder.objects.get(
                order_id=order_id,
                customer=request.user,
                status='pending'
            )
            
            # Check if payment already initiated
            existing_payment = PaymentTransaction.objects.filter(
                order=order,
                status__in=['pending', 'success']
            ).first()
            
            if existing_payment:
                if existing_payment.status == 'success':
                    return Response({
                        'error': 'Payment already completed for this order'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Return existing pending payment
                gateway = get_payment_gateway()
                payment_result = gateway.create_payment_session(order, request.user)
                
                if payment_result['success']:
                    return Response({
                        'payment_url': payment_result['payment_url'],
                        'transaction_id': existing_payment.transaction_id,
                        'order_id': str(order.order_id)
                    })
            
            # Create new payment transaction
            gateway = get_payment_gateway()
            payment_result = gateway.create_payment_session(order, request.user)
            
            if not payment_result['success']:
                return Response({
                    'error': payment_result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Save payment transaction
            payment_transaction = PaymentTransaction.objects.create(
                transaction_id=payment_result['transaction_id'],
                order=order,
                amount=order.total_amount,
                currency='BDT',
                status='pending',
                response_data=payment_result
            )
            
            return Response({
                'payment_url': payment_result['payment_url'],
                'transaction_id': payment_result['transaction_id'],
                'order_id': str(order.order_id),
                'message': 'Payment initiated successfully'
            })
            
        except RepairOrder.DoesNotExist:
            return Response({
                'error': 'Order not found or already processed'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Payment initiation error: {str(e)}")
            return Response({
                'error': 'Failed to initiate payment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentWebhookView(views.APIView):
    """
    SSLCommerz IPN (Instant Payment Notification) Webhook
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            logger.info(f"Webhook received: {request.data}")
            
            # FIX: SSLCommerz sends form-data, not JSON
            data = request.data.dict() if hasattr(request.data, 'dict') else dict(request.data)
            
            # Validate
            serializer = SSLCommerzWebhookSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            
            # Get IDs
            order_id = validated_data.get('value_a')
            event_id = validated_data.get('val_id')
            tran_id = validated_data.get('tran_id')
            
            if not all([order_id, event_id, tran_id]):
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check idempotency
            if PaymentEvent.objects.filter(event_id=event_id).exists():
                logger.info(f"Duplicate webhook: {event_id}")
                return Response({'status': 'already_processed'})
            
            # Find order
            try:
                order = RepairOrder.objects.get(order_id=order_id)
            except RepairOrder.DoesNotExist:
                logger.error(f"Order not found: {order_id}")
                return Response(
                    {'error': 'Order not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # FIX: SSLCommerz specific status checking
            # SSLCommerz sends: VALID, FAILED, CANCELLED, UNATTEMPTED, etc.
            status_value = validated_data.get('status', '').upper()
            
            with transaction.atomic():
                # Create payment event
                payment_event = PaymentEvent.objects.create(
                    event_id=event_id,
                    order=order,
                    payload=validated_data,
                    status='received'
                )
                
                # Get or create transaction
                payment_transaction, created = PaymentTransaction.objects.get_or_create(
                    transaction_id=tran_id,
                    defaults={
                        'order': order,
                        'amount': validated_data['amount'],
                        'currency': validated_data.get('currency', 'BDT'),
                        'status': 'pending',
                        'response_data': validated_data
                    }
                )
                
                payment_event.payment_transaction = payment_transaction
                payment_event.save()
                
                # Handle based on SSLCommerz status
                if status_value == 'VALID':
                    # Verify with SSLCommerz API
                    gateway = get_payment_gateway()
                    verification = gateway.validate_payment(event_id)
                    
                    if verification.get('status') == 'VALID':
                        payment_transaction.mark_as_success(
                            bank_transaction_id=validated_data.get('bank_tran_id'),
                            response_data=validated_data
                        )
                        payment_event.status = 'success'
                        payment_event.processed = True
                        payment_event.processed_at = timezone.now()
                        
                        logger.info(f"Payment successful for order: {order_id}")
                    else:
                        payment_transaction.status = 'failed'
                        payment_transaction.save()
                        payment_event.status = 'verification_failed'
                        
                elif status_value in ['FAILED', 'CANCELLED', 'UNATTEMPTED']:
                    payment_transaction.status = 'failed' if status_value == 'FAILED' else 'cancelled'
                    payment_transaction.response_data = validated_data
                    payment_transaction.save()
                    
                    # Update order
                    order.status = 'failed'
                    order.save()
                    
                    # TODO: Release stock back
                    
                    payment_event.status = 'failed'
                    payment_event.processed = True
                    payment_event.processed_at = timezone.now()
                
                payment_event.save()
            
            return Response({'status': 'processed'})
            
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentSuccessView(views.APIView):
    """
    Redirect URL after successful payment
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get parameters from SSLCommerz redirect
        tran_id = request.GET.get('tran_id')
        status = request.GET.get('status')
        
        try:
            if tran_id and status == 'VALID':
                # Find payment transaction
                payment = PaymentTransaction.objects.get(transaction_id=tran_id)
                
                # Redirect to frontend success page with order info
                frontend_url = urljoin(
                    settings.FRONTEND_URL,
                    f"/payment/success?order_id={payment.order.order_id}"
                )
                return redirect(frontend_url)
            
            # If payment failed or cancelled
            frontend_url = urljoin(
                settings.FRONTEND_URL,
                "/payment/failed"
            )
            return redirect(frontend_url)
            
        except PaymentTransaction.DoesNotExist:
            frontend_url = urljoin(
                settings.FRONTEND_URL,
                "/payment/error"
            )
            return redirect(frontend_url)


class PaymentFailView(views.APIView):
    """Redirect URL for failed payment"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        frontend_url = urljoin(
            settings.FRONTEND_URL,
            "/payment/failed"
        )
        return redirect(frontend_url)


class PaymentCancelView(views.APIView):
    """Redirect URL for cancelled payment"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        frontend_url = urljoin(
            settings.FRONTEND_URL,
            "/payment/cancelled"
        )
        return redirect(frontend_url)


class PaymentStatusView(generics.RetrieveAPIView):
    """Check payment status"""
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        order_id = self.kwargs.get('order_id')
        return PaymentTransaction.objects.filter(
            order__order_id=order_id,
            order__customer=self.request.user
        ).first()
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # If payment is pending, verify with SSLCommerz
        if instance.status == 'pending':
            gateway = get_payment_gateway()
            verification = gateway.validate_payment(instance.response_data.get('val_id', ''))
            
            if verification.get('status') == 'VALID':
                instance.mark_as_success(
                    verification.get('bank_tran_id'),
                    verification
                )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class PaymentHistoryView(generics.ListAPIView):
    """Get user's payment history"""
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PaymentTransaction.objects.filter(
            order__customer=self.request.user
        ).order_by('-created_at')
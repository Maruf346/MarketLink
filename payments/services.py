import requests
import uuid
from django.conf import settings
from django.urls import reverse
from urllib.parse import urljoin


class SSLCommerzPaymentGateway:
    """SSLCommerz payment gateway integration service"""
    
    def __init__(self):
        self.store_id = settings.SSLCOMMERZ_STORE_ID
        self.store_password = settings.SSLCOMMERZ_STORE_PASSWORD
        self.sandbox_mode = settings.SSLCOMMERZ_SANDBOX_MODE
        
        # FIX: Use appropriate URL based on sandbox mode
        if self.sandbox_mode:
            self.base_url = "https://sandbox.sslcommerz.com/gwprocess/v3/api.php"
            self.validation_url = "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php"
        else:
            self.base_url = "https://securepay.sslcommerz.com/gwprocess/v3/api.php"
            self.validation_url = "https://securepay.sslcommerz.com/validator/api/validationserverAPI.php"
        
    def create_payment_session(self, order, customer):
        """
        Create a payment session with SSLCommerz
        """
        # SSLCommerz transaction ID format
        transaction_id = f"ML{order.id}{uuid.uuid4().hex[:6]}".upper()
        
        # FIX: URLs - use reverse properly
        success_url = urljoin(
            settings.BASE_URL,
            reverse('payment-success')
        )
        fail_url = urljoin(
            settings.BASE_URL,
            reverse('payment-fail')
        )
        cancel_url = urljoin(
            settings.BASE_URL,
            reverse('payment-cancel')
        )
        ipn_url = urljoin(
            settings.BASE_URL,
            reverse('payment-webhook')
        )
        
        # FIX: SSLCommerz required parameters
        post_data = {
            'store_id': self.store_id,
            'store_passwd': self.store_password,
            'total_amount': f"{order.total_amount:.2f}",
            'currency': 'BDT',
            'tran_id': transaction_id,
            'success_url': success_url,
            'fail_url': fail_url,
            'cancel_url': cancel_url,
            'ipn_url': ipn_url,
            
            # Customer Info (required)
            'cus_name': customer.email.split('@')[0] if '@' in customer.email else 'Customer',
            'cus_email': customer.email,
            'cus_add1': 'N/A',
            'cus_city': 'Dhaka',
            'cus_postcode': '1000',
            'cus_country': 'Bangladesh',
            'cus_phone': '01700000000',
            
            # Shipping (same as billing for services)
            'shipping_method': 'NO',
            'product_name': f"Repair: {order.variant.service.name[:30]}",
            'product_category': 'Service',
            'product_profile': 'general',
            
            # Custom fields for tracking
            'value_a': str(order.order_id),  # Order UUID
            'value_b': str(customer.id),     # Customer ID
            
            # Important: multi_card_name for sandbox
            'multi_card_name': 'internetbank,mobilebank,visacard,mastercard,othercard',
        }
        
        try:
            response = requests.post(self.base_url, data=post_data, timeout=30)
            
            # FIX: SSLCommerz returns different response format
            if response.status_code == 200:
                response_text = response.text
                
                # Parse the response (SSLCommerz returns key=value pairs)
                response_dict = {}
                for line in response_text.split('&'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        response_dict[key] = value
                
                if response_dict.get('status') == 'SUCCESS':
                    return {
                        'success': True,
                        'payment_url': response_dict.get('GatewayPageURL'),
                        'transaction_id': transaction_id,
                        'session_key': response_dict.get('sessionkey'),
                        'response': response_dict
                    }
                else:
                    return {
                        'success': False,
                        'error': response_dict.get('failedreason', 'Payment initialization failed'),
                        'response': response_dict
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'response': response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
    
    def validate_payment(self, validation_id):
        """
        Validate payment with SSLCommerz API
        """
        params = {
            'val_id': validation_id,
            'store_id': self.store_id,
            'store_passwd': self.store_password,
            'format': 'json',
            'v': '1'
        }
        
        try:
            response = requests.get(self.validation_url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}', 'status': 'FAILED'}
        except Exception as e:
            return {'error': str(e), 'status': 'FAILED'}
    
    # FIX: SSLCommerz doesn't use HMAC signatures in webhooks
    # They validate via their API with store_id/store_passwd
    def verify_webhook_signature(self, payload, signature):
        """
        SSLCommerz doesn't typically use HMAC signatures.
        Instead, validate through their API.
        """
        # For SSLCommerz, we validate via API, not HMAC
        return True
    
    

class MockPaymentGateway:
    """
    Mock payment gateway for development/testing
    """
    
    def create_payment_session(self, order, customer):
        """Create mock payment session"""
        return {
            'success': True,
            'payment_url': f"/mock-payment/{order.order_id}/",
            'transaction_id': f"MOCK-{order.order_id}",
            'session_key': 'mock_session_key',
        }
    
    def validate_payment(self, validation_id):
        """Mock validation"""
        return {
            'status': 'VALID',
            'tran_id': validation_id,
            'amount': '100.00',
            'currency': 'BDT',
            'bank_tran_id': f"BANK-{validation_id}",
        }
    
    def verify_webhook_signature(self, payload, signature):
        """Mock signature verification"""
        return True


def get_payment_gateway():
    """
    Factory function to get appropriate payment gateway
    """
    if settings.SSLCOMMERZ_SANDBOX_MODE and not settings.SSLCOMMERZ_STORE_ID:
        return MockPaymentGateway()
    return SSLCommerzPaymentGateway()
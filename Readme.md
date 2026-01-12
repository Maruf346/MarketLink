# MarketLink - Multi-Vendor Marketplace Backend

[![Django](https://img.shields.io/badge/Django-4.2.16-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14.0-blue.svg)](https://www.django-rest-framework.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-yellow.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

A complete Django REST Framework backend for a multi-vendor marketplace connecting local repair shops with vehicle owners. Built with production-ready practices including concurrency handling, payment integration, and idempotent webhook processing.

## 📋 Table of Contents
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [Core Features](#-core-features)
- [Payment Integration](#-payment-integration)
- [Concurrency Handling](#-concurrency-handling)
- [Environment Variables](#-environment-variables)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [API Endpoints](#-api-endpoints)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

- **🔐 Custom User Model** with JWT authentication (Customer, Vendor, Admin roles)
- **🏪 Vendor Management** with business profiles and service offerings
- **🔧 Service Variants** with pricing, estimated time, and stock management
- **🛒 Order Processing** with concurrency-safe booking system
- **💳 Payment Integration** with SSLCommerz (sandbox & production)
- **🔔 Idempotent Webhook** processing for payment confirmation
- **🔄 Redis-based Locking** for preventing double bookings
- **📊 Admin Dashboard** with comprehensive management tools
- **📚 API Documentation** with Swagger/OpenAPI
- **🧪 Comprehensive Testing** suite

## 🛠 Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Django 4.2 + Django REST Framework |
| **Database** | PostgreSQL (Production) / SQLite (Development) |
| **Authentication** | JWT with SimpleJWT |
| **Caching & Locking** | Redis |
| **Payment Gateway** | SSLCommerz |
| **API Docs** | drf-spectacular (Swagger) |
| **Task Queue** | Celery (Optional) |
| **Containerization** | Docker & Docker Compose |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (SQLite for development)
- Redis 7+
- Virtual Environment

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd marketlink

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your configuration (see Environment Variables section)

# 5. Run migrations
python manage.py makemigrations
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Start development server
python manage.py runserver

# 8. Start Redis (in another terminal)
redis-server
```

## 📁 Project Structure

```
marketlink/
├── core/                          # Custom user model & authentication
│   ├── models.py                  # User model with roles
│   ├── serializers.py             # Auth serializers
│   ├── views.py                   # Auth endpoints
│   ├── permissions.py             # Role-based permissions
│   └── urls.py                    # Auth routes
│
├── vendors/                       # Vendor management
│   ├── models.py                  # VendorProfile, Service, ServiceVariant
│   ├── serializers.py             # Vendor & service serializers
│   ├── views.py                   # Vendor endpoints
│   ├── admin.py                   # Admin interface
│   └── urls.py                    # Vendor routes
│
├── orders/                        # Order management
│   ├── models.py                  # RepairOrder model
│   ├── serializers.py             # Order serializers
│   ├── views.py                  # Order endpoints with concurrency
│   ├── admin.py                  # Order admin
│   └── urls.py                   # Order routes
│
├── payments/                      # Payment integration
│   ├── models.py                 # PaymentTransaction, PaymentEvent
│   ├── serializers.py            # Payment serializers
│   ├── views.py                  # Payment endpoints & webhooks
│   ├── services.py               # SSLCommerz integration
│   ├── admin.py                  # Payment admin
│   └── urls.py                   # Payment routes
│
├── api/                          # API routing
│   └── urls.py                   # Combined URL configuration
│
├── marketlink/                   # Project settings
│   ├── settings.py              # Main settings
│   ├── urls.py                  # Main URL configuration
│   └── wsgi.py                  # WSGI configuration
│
├── static/                       # Static files
├── media/                        # Media uploads
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
└── README.md                    # This file
```

## 📚 API Documentation

### Interactive Documentation
Once the server is running, access the API documentation:

- **Swagger UI**: http://localhost:8000/api/docs/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### Postman Collection
Import the Postman collection from `docs/MarketLink.postman_collection.json` for complete API testing.

## 🎯 Core Features

### 1. Custom User Model with Roles
```python
# Roles: customer, vendor, admin
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('admin', 'Admin'),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
```

### 2. Service & Variant Management
- Vendors can create services with multiple variants (Basic, Premium, Express)
- Each variant has price, estimated minutes, and stock count
- Real-time stock management with concurrency protection

### 3. Order Flow
```
Customer → Browse Services → Select Variant → 
Create Order (with stock lock) → Initiate Payment → 
Redirect to Payment Gateway → Webhook Processing → 
Order Confirmation → Vendor Notification
```

## 💳 Payment Integration

### SSLCommerz Configuration
The system integrates with SSLCommerz for payment processing:

#### Sandbox Testing
```env
SSLCOMMERZ_STORE_ID=testbox
SSLCOMMERZ_STORE_PASSWORD=qwerty
SSLCOMMERZ_SANDBOX_MODE=True
```

#### Test Cards
| Card Number | Card Type | Expiry | CVV |
|-------------|-----------|---------|-----|
| 4111111111111111 | Visa | Any future date | 123 |
| 5500000000000004 | MasterCard | Any future date | 123 |

#### Payment Flow
1. **Order Creation**: Customer creates order with status 'pending'
2. **Payment Initiation**: System generates SSLCommerz payment URL
3. **Redirect**: Customer redirected to SSLCommerz payment page
4. **Payment**: Customer completes payment
5. **Webhook**: SSLCommerz sends IPN to `/api/payments/webhook/`
6. **Processing**: System validates and updates order status

### Webhook Security
- **Idempotency**: Each payment event processed only once
- **Validation**: Payment verification via SSLCommerz API
- **Signature Verification**: HMAC signature validation (optional)

## 🔒 Concurrency Handling

### The Problem
When multiple customers try to book the same service variant with limited stock simultaneously, the system must prevent double-booking.

### Our Solution: Redis-based Distributed Locking

#### Implementation Approach
```python
# Simplified flow in orders/views.py
def create_order(request):
    variant_id = request.data['variant_id']
    lock_key = f"lock:variant:{variant_id}"
    
    # Try to acquire lock
    lock_acquired = redis_client.setnx(lock_key, "locked")
    if not lock_acquired:
        return Response({"error": "Service is being booked"}, status=409)
    
    try:
        # Set lock expiration
        redis_client.expire(lock_key, 10)
        
        # Check and decrement stock atomically
        variant = ServiceVariant.objects.select_for_update().get(id=variant_id)
        if variant.stock > 0:
            variant.stock -= 1
            variant.save()
            # Create order...
        else:
            raise ValidationError("Out of stock")
            
    finally:
        # Release lock
        redis_client.delete(lock_key)
```

#### Key Features
1. **Distributed Locking**: Works across multiple Django instances
2. **Timeout Protection**: Automatic lock release after 10 seconds
3. **Atomic Operations**: Database-level locking with `select_for_update()`
4. **Fallback Strategy**: Database transaction rollback on failure

#### Stock Reservation Flow
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Check Stock   │───▶│  Acquire Lock   │───▶│ Decrement Stock │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                      │                      │
        ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Stock > 0?    │    │  Lock Success?  │    │ Create Order    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                      │                      │
        ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      Yes        │    │      Yes        │    │  Release Lock   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## ⚙️ Environment Variables

Create a `.env` file in the project root:

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DB_NAME=marketlink_db
DB_USER=marketlink_user
DB_PASSWORD=marketlink_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=86400

# SSLCommerz
SSLCOMMERZ_STORE_ID=your_store_id
SSLCOMMERZ_STORE_PASSWORD=your_store_password
SSLCOMMERZ_SANDBOX_MODE=True

# Webhook
WEBHOOK_SECRET=your-webhook-secret
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Email (for invoices)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```


## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Use PostgreSQL database
- [ ] Configure SSL/TLS certificates
- [ ] Set up Redis for production
- [ ] Configure production web server (Nginx/Gunicorn)
- [ ] Set up monitoring (Sentry, New Relic)
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline


## 📡 API Endpoints

### Authentication (`/api/auth/`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/register/` | Register new user | No |
| POST | `/login/` | Login with JWT | No |
| POST | `/logout/` | Logout (blacklist token) | Yes |
| GET | `/profile/` | Get user profile | Yes |
| POST | `/change-password/` | Change password | Yes |
| POST | `/token/refresh/` | Refresh JWT token | No |

### Vendors (`/api/vendors/`)
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| GET | `/profile/` | Get vendor profile | Yes | Vendor |
| PUT | `/profile/` | Update vendor profile | Yes | Vendor |
| GET | `/services/` | List vendor services | Yes | Vendor |
| POST | `/services/` | Create service | Yes | Vendor |
| GET | `/public/services/` | List public services | No | - |

### Orders (`/api/orders/`)
| Method | Endpoint | Description | Auth Required | Role |
|--------|----------|-------------|---------------|------|
| POST | `/create/` | Create new order | Yes | Customer |
| GET | `/my-orders/` | List customer orders | Yes | Customer |
| GET | `/vendor-orders/` | List vendor orders | Yes | Vendor |

### Payments (`/api/payments/`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/initiate/<order_id>/` | Initiate payment | Yes |
| GET | `/status/<order_id>/` | Check payment status | Yes |
| GET | `/history/` | Payment history | Yes |
| POST | `/webhook/` | SSLCommerz IPN webhook | No |

## 🔄 Background Tasks

### Celery Configuration (Optional)
```python
# config/celery.py
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketlink.settings')
app = Celery('marketlink')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

### Scheduled Tasks
1. **Stock Reservation Cleanup**: Release expired stock reservations
2. **Invoice Generation**: Generate and send invoices after payment
3. **Order Status Updates**: Auto-cancel unpaid orders after timeout
4. **Vendor Notifications**: Notify vendors of new orders

## 📊 Monitoring & Logging

### Logging Configuration
```python
# settings/production.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/marketlink/django.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
        'marketlink': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Health Check Endpoint
```http
GET /health/
Response: {"status": "healthy", "timestamp": "2024-01-13T12:00:00Z"}
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Use meaningful commit messages
- Add type hints where appropriate

### Code Quality
```bash
# Run code formatter
black .

# Run linter
flake8

# Run type checking
mypy .

# Check import order
isort .
```

## 📄 License

This project is proprietary software. All rights reserved.

## 📞 Support

For support, please contact:
- **Email**: support@marketlink.com
- **Issues**: [GitHub Issues](https://github.com/maruf346/marketlink/issues)
- **Documentation**: [Read the Docs](https://marketlink.readthedocs.io/)

## 🙏 Acknowledgments

- Django REST Framework team
- SSLCommerz for payment gateway
- Redis for caching and locking
- All contributors and testers

---

*Last Updated: January 13, 2026*
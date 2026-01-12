from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    path('auth/', include('core.urls')),
    path('vendors/', include('vendors.urls')),
    path('orders/', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema')),
]

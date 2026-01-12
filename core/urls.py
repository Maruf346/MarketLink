from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Token management
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # User profile
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('whoami/', views.WhoAmIView.as_view(), name='whoami'),
    
    # Admin only endpoints
    path('users/', views.ListUsersView.as_view(), name='list_users'),
    path('users/<int:pk>/toggle-active/', views.ActivateDeactivateUserView.as_view(), name='toggle_user_active'),
    path('users/<int:pk>/update-role/', views.UpdateUserRoleView.as_view(), name='update_user_role'),
]
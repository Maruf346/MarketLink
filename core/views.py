from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.translation import gettext_lazy as _

from .models import User
from .serializers import *


class RegisterView(generics.CreateAPIView):
    """
    Register a new user.
    POST /api/auth/register/
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user, context=self.get_serializer_context()).data,
            'message': 'Registration successful.'
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Login view with JWT tokens.
    POST /api/auth/login/
    """
    serializer_class = CustomTokenObtainPairSerializer


class LoginView(APIView):
    """
    Alternative login view using custom serializer.
    POST /api/auth/login/ (alternative)
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer  # Add this line
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user, context={'request': request}).data,
            'message': 'Login successful.'
        })


class LogoutView(APIView):
    """
    Logout view to blacklist refresh token.
    POST /api/auth/logout/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None  # Explicitly set to None since we don't need one
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Logout successful.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveAPIView):
    """
    Get current user profile.
    GET /api/auth/profile/
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    Change user password.
    POST /api/auth/change-password/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer  # Add this line
    
    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Invalidate all existing tokens
        RefreshToken.for_user(user)
        
        return Response({
            'message': 'Password changed successfully.'
        })


class WhoAmIView(APIView):
    """
    Get current user information (simple version).
    GET /api/auth/whoami/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer  # Add this line
    
    def get(self, request):
        serializer = self.serializer_class(request.user, context={'request': request})
        return Response(serializer.data)


class ListUsersView(generics.ListAPIView):
    """
    List all users (admin only).
    GET /api/auth/users/
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['role', 'is_active']
    search_fields = ['email']


class ActivateDeactivateUserView(APIView):
    """
    Activate or deactivate a user (admin only).
    POST /api/auth/users/{id}/toggle-active/
    """
    permission_classes = [permissions.IsAdminUser]
    serializer_class = None  # Explicitly set to None
    
    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            
            # Admin cannot deactivate themselves
            if user == request.user:
                return Response(
                    {"error": "You cannot deactivate your own account."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.is_active = not user.is_active
            user.save()
            
            action = "activated" if user.is_active else "deactivated"
            return Response({
                "message": f"User {action} successfully.",
                "user": UserSerializer(user).data
            })
            
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class UpdateUserRoleView(APIView):
    """
    Update user role (admin only).
    POST /api/auth/users/{id}/update-role/
    """
    permission_classes = [permissions.IsAdminUser]
    serializer_class = None  # Explicitly set to None
    
    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            new_role = request.data.get('role')
            
            # Validate role
            valid_roles = [choice[0] for choice in User.ROLE_CHOICES]
            if new_role not in valid_roles:
                return Response(
                    {"error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Admin cannot change their own role
            if user == request.user:
                return Response(
                    {"error": "You cannot change your own role."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.role = new_role
            user.save()
            
            return Response({
                "message": f"User role updated to {new_role}.",
                "user": UserSerializer(user).data
            })
            
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
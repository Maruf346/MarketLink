from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(BaseBackend):
    """
    Custom authentication backend that uses email.
    """
    
    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None:
            email = kwargs.get('email')
        
        try:
            # Try to find user by email (case-insensitive)
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce timing attacks
            User().set_password(password)
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False.
        """
        return user.is_active
    
    def get_user(self, user_id):
        """
        Get user by ID.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
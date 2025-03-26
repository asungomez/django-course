"""
Serializers for the User API view
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers
from core.models import User
from typing import Any


class UserSerializer(serializers.ModelSerializer[User]):
    """Serializer for the user object"""

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            )
        read_only_fields = ("id", "email", "username")

    def create(self, validated_data: dict[str, Any]) -> User:
        """Create and return a new user"""
        return get_user_model().objects.create_user(**validated_data)

    def find_by_email(self, email: str) -> User:
        """Find a user by email"""
        email_parts = email.lower().split("@")
        if len(email_parts) != 2:
            raise ValueError("Invalid email")
        username = email_parts[0]
        return get_user_model().objects.get(username=username)

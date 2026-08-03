from django.contrib.auth import authenticate
from rest_framework import serializers

from .exceptions import InvalidCredentials
from .models import User
from .security import (
    clear_login_failures,
    enforce_login_rate_limit,
    get_client_ip,
    normalize_email,
    record_login_failure,
)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False, write_only=True)

    def validate(self, attrs):
        request = self.context.get("request")
        email = normalize_email(attrs["email"])
        ip_address = get_client_ip(request)
        enforce_login_rate_limit(scope="api", ip_address=ip_address, email=email)
        user = authenticate(
            request=request,
            email=email,
            password=attrs["password"],
        )
        if user is None or not user.is_active:
            record_login_failure(scope="api", ip_address=ip_address, email=email)
            raise InvalidCredentials()
        clear_login_failures(scope="api", ip_address=ip_address, email=email)
        attrs["user"] = user
        return attrs


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "display_name", "is_staff")

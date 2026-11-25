from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя с хешированием пароля."""

    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ("id", "email", "password", "tg_chat_id", "tg_username")

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            tg_chat_id=validated_data.get("tg_chat_id"),
            tg_username=validated_data.get("tg_username"),
        )

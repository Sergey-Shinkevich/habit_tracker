from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UserModelAndManagerTests(APITestCase):
    """Тесты кастомной модели пользователя и UserManager."""

    def test_create_user_normalizes_email_and_hashes_password(self):
        user = User.objects.create_user(
            email="User@Example.COM",
            password="StrongPassword123!",
            tg_chat_id=123456789,
            tg_username="test_user",
        )
        self.assertEqual(user.email, "User@example.com")
        self.assertTrue(user.check_password("StrongPassword123!"))
        self.assertNotEqual(user.password, "StrongPassword123!")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.tg_chat_id, 123456789)
        self.assertEqual(user.tg_username, "test_user")
        self.assertEqual(str(user), user.email)

    def test_create_user_without_email_raises_value_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="StrongPassword123!")

    def test_create_superuser_sets_staff_and_superuser_flags(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPassword123!",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_create_superuser_without_staff_raises_value_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="badadmin@example.com",
                password="AdminPassword123!",
                is_staff=False,
            )

    def test_create_superuser_without_superuser_raises_value_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="badadmin2@example.com",
                password="AdminPassword123!",
                is_superuser=False,
            )


class UserAuthAPITests(APITestCase):
    """Тесты регистрации и получения/обновления JWT-токенов."""

    def test_register_user_success_and_hides_password(self):
        url = reverse("user:register")
        payload = {
            "email": "newuser@example.com",
            "password": "secret123",
            "tg_chat_id": 987654321,
            "tg_username": "newhabit_user",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)
        self.assertEqual(response.data["email"], "newuser@example.com")

        user = User.objects.get(email="newuser@example.com")
        self.assertTrue(user.check_password("secret123"))
        self.assertEqual(user.tg_chat_id, 987654321)

    def test_register_user_short_password_fails(self):
        url = reverse("user:register")
        payload = {
            "email": "shortpass@example.com",
            "password": "123",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_register_duplicate_email_fails(self):
        User.objects.create_user(email="dupe@example.com", password="Password123!")
        url = reverse("user:register")
        payload = {
            "email": "dupe@example.com",
            "password": "AnotherPassword123!",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_and_refresh_jwt_tokens(self):
        User.objects.create_user(email="jwtuser@example.com", password="JwtPassword123!")

        login_url = reverse("user:login")
        login_resp = self.client.post(
            login_url,
            {"email": "jwtuser@example.com", "password": "JwtPassword123!"},
            format="json",
        )
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_resp.data)
        self.assertIn("refresh", login_resp.data)

        refresh_url = reverse("user:token_refresh")
        refresh_resp = self.client.post(
            refresh_url,
            {"refresh": login_resp.data["refresh"]},
            format="json",
        )
        self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_resp.data)

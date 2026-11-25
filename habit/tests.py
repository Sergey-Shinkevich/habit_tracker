from datetime import time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.test import APITestCase

from habit.models import Habit
from habit.serializers import HabitSerializer
from habit.validators import validate_habit_data

User = get_user_model()


class HabitValidationTests(APITestCase):
    """Тесты правил валидации привычек."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="StrongPassword123!",
        )
        self.pleasant_habit = Habit.objects.create(
            owner=self.user,
            place="Диван",
            time=time(20, 0),
            action="Посмотреть серию",
            is_pleasant=True,
            period=1,
            length=60,
        )
        self.useful_habit = Habit.objects.create(
            owner=self.user,
            place="Кухня",
            time=time(8, 0),
            action="Выпить стакан воды",
            is_pleasant=False,
            period=1,
            length=30,
        )

    def test_valid_useful_habit_with_reward(self):
        data = {
            "place": "Дом",
            "time": time(9, 0),
            "action": "Сделать зарядку",
            "is_pleasant": False,
            "linked": None,
            "reward": "Чашка кофе",
            "period": 1,
            "length": 120,
            "is_public": True,
        }
        validate_habit_data(data)

    def test_valid_useful_habit_with_pleasant_linked(self):
        data = {
            "place": "Дом",
            "time": time(19, 0),
            "action": "Почитать книгу",
            "is_pleasant": False,
            "linked": self.pleasant_habit,
            "reward": None,
            "period": 7,
            "length": 45,
        }
        validate_habit_data(data)

    def test_cannot_set_both_reward_and_linked(self):
        data = {
            "linked": self.pleasant_habit,
            "reward": "Шоколадка",
            "length": 30,
            "period": 1,
        }
        with self.assertRaises(DRFValidationError):
            validate_habit_data(data)

    def test_length_must_be_between_1_and_120_seconds(self):
        for bad_length in (0, 121):
            with self.subTest(length=bad_length):
                with self.assertRaises(DRFValidationError):
                    validate_habit_data({"length": bad_length, "period": 1})

    def test_linked_habit_must_be_pleasant(self):
        with self.assertRaises(DRFValidationError):
            validate_habit_data({"linked": self.useful_habit, "period": 1})

    def test_pleasant_habit_cannot_have_reward_or_linked(self):
        with self.assertRaises(DRFValidationError):
            validate_habit_data({"is_pleasant": True, "reward": "Отдых", "period": 1})

        with self.assertRaises(DRFValidationError):
            validate_habit_data({"is_pleasant": True, "linked": self.pleasant_habit, "period": 1})

    def test_period_must_be_between_1_and_7_days(self):
        for bad_period in (0, 8):
            with self.subTest(period=bad_period):
                with self.assertRaises(DRFValidationError):
                    validate_habit_data({"period": bad_period, "length": 30})

    def test_model_clean_runs_validation(self):
        habit = Habit(
            owner=self.user,
            place="Офис",
            time=time(10, 0),
            action="Разминка",
            is_pleasant=True,
            reward="Чай",
            period=1,
            length=20,
        )
        with self.assertRaises((DRFValidationError, DjangoValidationError)):
            habit.clean()

    def test_serializer_validates_data(self):
        serializer = HabitSerializer(
            data={
                "place": "Офис",
                "time": "10:00:00",
                "action": "Разминка",
                "is_pleasant": False,
                "linked": self.pleasant_habit.id,
                "reward": "Чай",
                "period": 1,
                "length": 20,
            }
        )
        self.assertFalse(serializer.is_valid())


class HabitAPITests(APITestCase):
    """Тесты CRUD, прав доступа, публичных привычек и пагинации."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="StrongPassword123!",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="StrongPassword123!",
        )
        self.client.force_authenticate(user=self.user)

        self.my_private_habit = Habit.objects.create(
            owner=self.user,
            place="Дом",
            time=time(7, 30),
            action="Медитация",
            is_pleasant=False,
            period=1,
            length=60,
            is_public=False,
        )
        self.other_public_habit = Habit.objects.create(
            owner=self.other_user,
            place="Парк",
            time=time(18, 0),
            action="Пробежка",
            is_pleasant=False,
            period=2,
            length=90,
            is_public=True,
        )
        self.other_private_habit = Habit.objects.create(
            owner=self.other_user,
            place="Комната",
            time=time(22, 0),
            action="Дневник",
            is_pleasant=True,
            period=1,
            length=40,
            is_public=False,
        )

    def test_unauthenticated_user_gets_401(self):
        self.client.force_authenticate(user=None)
        url = reverse("habit:habit-list")
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_list_returns_only_current_user_habits(self):
        url = reverse("habit:habit-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"] if "results" in response.data else response.data
        ids = [item["id"] for item in results]
        self.assertIn(self.my_private_habit.id, ids)
        self.assertNotIn(self.other_public_habit.id, ids)
        self.assertNotIn(self.other_private_habit.id, ids)

    def test_public_list_returns_only_public_habits(self):
        url = reverse("habit:habit-public-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"] if "results" in response.data else response.data
        ids = [item["id"] for item in results]
        self.assertIn(self.other_public_habit.id, ids)
        self.assertNotIn(self.my_private_habit.id, ids)
        self.assertNotIn(self.other_private_habit.id, ids)

    def test_create_habit_sets_owner_automatically(self):
        url = reverse("habit:habit-create")
        payload = {
            "place": "Кухня",
            "time": "08:15:00",
            "action": "Выпить воду",
            "is_pleasant": False,
            "period": 1,
            "length": 15,
            "is_public": True,
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created = Habit.objects.get(id=response.data["id"])
        self.assertEqual(created.owner, self.user)

    def test_owner_can_retrieve_update_and_delete_own_habit(self):
        detail_url = reverse("habit:habit-retrieve", kwargs={"pk": self.my_private_habit.pk})
        update_url = reverse("habit:habit-update", kwargs={"pk": self.my_private_habit.pk})
        delete_url = reverse("habit:habit-delete", kwargs={"pk": self.my_private_habit.pk})

        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_200_OK)

        patch_resp = self.client.patch(update_url, {"action": "Утренняя медитация"}, format="json")
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.my_private_habit.refresh_from_db()
        self.assertEqual(self.my_private_habit.action, "Утренняя медитация")

        del_resp = self.client.delete(delete_url)
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Habit.objects.filter(pk=self.my_private_habit.pk).exists())

    def test_cannot_update_or_delete_other_users_habit(self):
        update_url = reverse("habit:habit-update", kwargs={"pk": self.other_public_habit.pk})
        delete_url = reverse("habit:habit-delete", kwargs={"pk": self.other_public_habit.pk})

        self.assertEqual(
            self.client.patch(update_url, {"action": "Взлом"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.delete(delete_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_pagination_on_habit_list(self):
        for i in range(6):
            Habit.objects.create(
                owner=self.user,
                place="Дом",
                time=time(10, i),
                action=f"Привычка {i}",
                is_pleasant=False,
                period=1,
                length=30,
            )

        url = reverse("habit:habit-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNotNone(response.data["next"])

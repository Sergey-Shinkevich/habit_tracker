from datetime import datetime, time, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from habit.models import Habit
from telegram_bot.services import send_telegram_message
from telegram_bot.tasks import send_habit_reminders

User = get_user_model()


class TelegramServiceTests(APITestCase):
    """Тесты функции отправки сообщений в Telegram."""

    @override_settings(TG_BOT_TOKEN="123456:ABC-DEF")
    @patch("telegram_bot.services.requests.post")
    def test_send_telegram_message_posts_to_bot_api(self, mock_post):
        send_telegram_message(777888999, "Тестовое напоминание")

        mock_post.assert_called_once_with(
            "https://api.telegram.org/bot123456:ABC-DEF/sendMessage",
            json={"chat_id": 777888999, "text": "Тестовое напоминание"},
            timeout=10,
        )

    @override_settings(TG_BOT_TOKEN="")
    @patch("telegram_bot.services.requests.post")
    def test_send_telegram_message_skips_without_token(self, mock_post):
        send_telegram_message(777888999, "Тестовое напоминание")
        mock_post.assert_not_called()

    @override_settings(TG_BOT_TOKEN="123456:ABC-DEF")
    @patch("telegram_bot.services.requests.post")
    def test_send_telegram_message_skips_without_chat_id(self, mock_post):
        send_telegram_message(None, "Тестовое напоминание")
        mock_post.assert_not_called()


class HabitReminderTaskTests(APITestCase):
    """Тесты периодической задачи send_habit_reminders."""

    def setUp(self):
        self.tz = ZoneInfo("Europe/Moscow")
        self.fixed_now = datetime(2026, 11, 26, 8, 30, 0, tzinfo=self.tz)
        self.today = self.fixed_now.date()

        self.user_with_tg = User.objects.create_user(
            email="tguser@example.com",
            password="StrongPassword123!",
            tg_chat_id=555111222,
        )
        self.user_without_tg = User.objects.create_user(
            email="notg@example.com",
            password="StrongPassword123!",
            tg_chat_id=None,
        )
        self.pleasant_habit = Habit.objects.create(
            owner=self.user_with_tg,
            place="Диван",
            time=time(21, 0),
            action="Послушать музыку",
            is_pleasant=True,
            period=1,
            length=60,
        )

    @patch("telegram_bot.tasks.send_telegram_message")
    @patch("telegram_bot.tasks.timezone.localtime")
    def test_sends_reminder_and_updates_last_sent_when_time_matches(self, mock_localtime, mock_send):
        mock_localtime.return_value = self.fixed_now

        habit_with_reward = Habit.objects.create(
            owner=self.user_with_tg,
            place="Кухня",
            time=time(8, 30),
            action="Выпить стакан воды",
            reward="Кофе",
            period=1,
            length=20,
        )
        habit_with_linked = Habit.objects.create(
            owner=self.user_with_tg,
            place="Комната",
            time=time(8, 30),
            action="Сделать зарядку",
            linked=self.pleasant_habit,
            period=2,
            length=90,
        )
        # Привычка с другим временем — должна быть проигнорирована
        Habit.objects.create(
            owner=self.user_with_tg,
            place="Офис",
            time=time(9, 0),
            action="Проверить задачи",
            period=1,
            length=30,
        )
        # Пользователь без tg_chat_id — должен быть проигнорирован
        Habit.objects.create(
            owner=self.user_without_tg,
            place="Дом",
            time=time(8, 30),
            action="Почитать",
            period=1,
            length=45,
        )

        send_habit_reminders()

        self.assertEqual(mock_send.call_count, 2)
        sent_calls = {call.args[0]: call.args[1] for call in mock_send.call_args_list}
        self.assertIn(555111222, sent_calls)

        all_messages = "\n".join(call.args[1] for call in mock_send.call_args_list)
        self.assertIn("Выпить стакан воды", all_messages)
        self.assertIn("Вознаграждение: Кофе", all_messages)
        self.assertIn("Сделать зарядку", all_messages)
        self.assertIn("Приятная привычка после: Послушать музыку", all_messages)

        habit_with_reward.refresh_from_db()
        habit_with_linked.refresh_from_db()
        self.assertEqual(habit_with_reward.last_sent, self.today)
        self.assertEqual(habit_with_linked.last_sent, self.today)

    @patch("telegram_bot.tasks.send_telegram_message")
    @patch("telegram_bot.tasks.timezone.localtime")
    def test_skips_habit_when_period_has_not_elapsed(self, mock_localtime, mock_send):
        mock_localtime.return_value = self.fixed_now

        # Период 3 дня, отправляли 1 день назад -> пропускаем
        habit_too_early = Habit.objects.create(
            owner=self.user_with_tg,
            place="Балкон",
            time=time(8, 30),
            action="Полить цветы",
            period=3,
            length=40,
            last_sent=self.today - timedelta(days=1),
        )
        # Период 2 дня, отправляли 2 дня назад -> days_passed == 2 >= period -> отправляем
        habit_due = Habit.objects.create(
            owner=self.user_with_tg,
            place="Стол",
            time=time(8, 30),
            action="Разобрать почту",
            period=2,
            length=50,
            last_sent=self.today - timedelta(days=2),
        )

        send_habit_reminders()

        mock_send.assert_called_once()
        self.assertIn("Разобрать почту", mock_send.call_args.args[1])

        habit_too_early.refresh_from_db()
        habit_due.refresh_from_db()
        self.assertEqual(habit_too_early.last_sent, self.today - timedelta(days=1))
        self.assertEqual(habit_due.last_sent, self.today)

from celery import shared_task
from django.utils import timezone

from habit.models import Habit
from telegram_bot.services import send_telegram_message


@shared_task
def send_habit_reminders():
    """Проверяет привычки на текущую минуту и отправляет напоминания в Telegram."""
    now = timezone.localtime()
    today = now.date()

    habits = Habit.objects.select_related("owner").filter(
        owner__tg_chat_id__isnull=False,
        time__hour=now.hour,
        time__minute=now.minute,
    )

    for habit in habits:
        if habit.last_sent is not None:
            days_passed = (today - habit.last_sent).days
            if days_passed < habit.period:
                continue

        message = f"Напоминание о привычке!\nДействие: {habit.action}\nМесто: {habit.place}\nВремя на выполнение: {habit.length} сек."
        if habit.reward:
            message += f"\nВознаграждение: {habit.reward}"
        elif habit.linked:
            message += f"\nПриятная привычка после: {habit.linked.action}"

        send_telegram_message(habit.owner.tg_chat_id, message)
        habit.last_sent = today
        habit.save(update_fields=["last_sent"])

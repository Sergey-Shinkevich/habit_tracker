from django.conf import settings
from django.db import models

from habit.validators import validate_habit_data


class Habit(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habits",
        verbose_name="Пользователь",
    )
    place = models.CharField(max_length=255, verbose_name="Место")
    time = models.TimeField(verbose_name="Время")
    action = models.CharField(max_length=255, verbose_name="Действие")
    is_pleasant = models.BooleanField(default=False, verbose_name="Признак приятной привычки")
    linked = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_habits",
        verbose_name="Связанная привычка",
    )
    period = models.PositiveIntegerField(default=1, verbose_name="Периодичность (в днях)")
    reward = models.CharField(max_length=255, null=True, blank=True, verbose_name="Вознаграждение")
    length = models.PositiveIntegerField(verbose_name="Время выполнения (в секундах)")
    is_public = models.BooleanField(default=False, verbose_name="Признак публичности")

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.action} в {self.time} ({self.place})"

    def clean(self):
        validate_habit_data({}, instance=self)

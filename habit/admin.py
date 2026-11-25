from django.contrib import admin

from habit.models import Habit


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "action",
        "time",
        "place",
        "period",
        "length",
        "is_pleasant",
        "is_public",
    )
    list_filter = ("is_pleasant", "is_public", "period")
    search_fields = ("action", "place", "reward", "owner__email")
    autocomplete_fields = ("owner", "linked")

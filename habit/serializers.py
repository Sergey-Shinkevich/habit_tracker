from rest_framework import serializers

from habit.models import Habit
from habit.validators import validate_habit_data


class HabitSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.email")

    class Meta:
        model = Habit
        fields = (
            "id",
            "owner",
            "place",
            "time",
            "action",
            "is_pleasant",
            "linked",
            "period",
            "reward",
            "length",
            "is_public",
        )

    def validate(self, attrs):
        validate_habit_data(attrs, instance=self.instance)
        return attrs
from rest_framework.serializers import ValidationError


def _get_value(data, instance, field_name, default=None):
    """Достаёт значение поля из данных запроса/формы или из текущего объекта."""
    if field_name in data:
        return data[field_name]
    if instance is not None:
        return getattr(instance, field_name, default)
    return default


def validate_habit_data(data, instance=None):
    """Комплексная валидация привычки для сериализаторов и модели."""
    is_pleasant = _get_value(data, instance, "is_pleasant", False)
    linked = _get_value(data, instance, "linked")
    reward = _get_value(data, instance, "reward")
    period = _get_value(data, instance, "period", 1)
    length = _get_value(data, instance, "length")

    if reward and linked:
        raise ValidationError(
            "Нельзя одновременно указывать вознаграждение и связанную привычку."
        )

    if length is not None and (length <= 0 or length > 120):
        raise ValidationError(
            "Время выполнения должно быть от 1 до 120 секунд."
        )

    if linked is not None and not linked.is_pleasant:
        raise ValidationError(
            "В связанные привычки можно выбрать только привычку с признаком приятной."
        )

    if is_pleasant and (reward or linked is not None):
        raise ValidationError(
            "У приятной привычки не может быть вознаграждения или связанной привычки."
        )

    if period is not None and (period < 1 or period > 7):
        raise ValidationError(
            "Периодичность выполнения должна быть от 1 до 7 дней."
        )
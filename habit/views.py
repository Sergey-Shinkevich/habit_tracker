from rest_framework import generics, permissions

from habit.models import Habit
from habit.pagination import HabitPagination
from habit.permissions import IsOwner
from habit.serializers import HabitSerializer


class HabitListView(generics.ListAPIView):
    """Список привычек текущего пользователя с пагинацией."""

    serializer_class = HabitSerializer
    pagination_class = HabitPagination
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Habit.objects.filter(owner=self.request.user)


class HabitPublicListView(generics.ListAPIView):
    """Список публичных привычек."""

    serializer_class = HabitSerializer
    pagination_class = HabitPagination
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Habit.objects.filter(is_public=True)


class HabitCreateView(generics.CreateAPIView):
    """Создание привычки."""

    serializer_class = HabitSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class HabitRetrieveView(generics.RetrieveAPIView):
    """Просмотр привычки владельцем."""

    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwner)


class HabitUpdateView(generics.UpdateAPIView):
    """Редактирование привычки владельцем."""

    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwner)


class HabitDestroyView(generics.DestroyAPIView):
    """Удаление привычки владельцем."""

    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwner)


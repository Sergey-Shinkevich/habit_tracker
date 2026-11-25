from django.urls import path

from habit.views import (
    HabitCreateView,
    HabitDestroyView,
    HabitListView,
    HabitPublicListView,
    HabitRetrieveView,
    HabitUpdateView,
)

app_name = "habit"

urlpatterns = [
    path("habits/", HabitListView.as_view(), name="habit-list"),
    path("habits/public/", HabitPublicListView.as_view(), name="habit-public-list"),
    path("habits/create/", HabitCreateView.as_view(), name="habit-create"),
    path("habits/<int:pk>/", HabitRetrieveView.as_view(), name="habit-retrieve"),
    path("habits/<int:pk>/update/", HabitUpdateView.as_view(), name="habit-update"),
    path("habits/<int:pk>/delete/", HabitDestroyView.as_view(), name="habit-delete"),
]

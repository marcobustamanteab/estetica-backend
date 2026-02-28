# appointments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet, send_reminders

router = DefaultRouter()
router.register(r'', AppointmentViewSet)

urlpatterns = [
    path('reminders/send/', send_reminders, name='send-reminders'),
    path('', include(router.urls)),
]
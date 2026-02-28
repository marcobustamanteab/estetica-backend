# appointments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet, send_reminders
from .public_views import public_business_info, public_available_times, public_create_appointment

router = DefaultRouter()
router.register(r'', AppointmentViewSet)

urlpatterns = [
    path('reminders/send/', send_reminders, name='send-reminders'),
    path('public/<slug:slug>/', public_business_info, name='public-business-info'),
    path('public/<slug:slug>/times/', public_available_times, name='public-available-times'),
    path('public/<slug:slug>/book/', public_create_appointment, name='public-create-appointment'),
    path('', include(router.urls)),
]
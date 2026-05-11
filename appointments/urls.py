# appointments/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet, send_reminders, test_email, test_zapier
from .public_views import public_business_info, public_available_times, public_create_appointment

router = DefaultRouter()
router.register(r'', AppointmentViewSet)

urlpatterns = [
    path('reminders/send/', send_reminders, name='send-reminders'),
    path('test-email/', test_email, name='test-email'),
    path('test-zapier/', test_zapier, name='test-zapier'),
    path('public/<slug:slug>/', public_business_info, name='public-business-info'),
    path('public/<slug:slug>/times/', public_available_times, name='public-available-times'),
    path('public/<slug:slug>/book/', public_create_appointment, name='public-create-appointment'),
    path('', include(router.urls)),
]

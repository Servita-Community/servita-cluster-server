# backend/api/urls.py
from django.urls import path
from .views import create_scan, get_scans, update_device_status, get_device_statuses

urlpatterns = [
    path('scans/', create_scan, name='create_scan'),
    path('scans/reports/', get_scans, name='get_scans'),
    path('devices/statuses/', get_device_statuses, name='get_device_statuses'),  # New endpoint to get all device statuses
    path('devices/<str:mac_address>/status/', update_device_status, name='update_device_status'),
]

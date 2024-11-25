from django.urls import path
from .views import (
    create_scan, get_scans, update_device_status, get_device_statuses,
    set_ota_server, set_led_color, connect_network, trigger_deep_sleep, set_stream_settings
)

urlpatterns = [
    path('scans/', create_scan, name='create_scan'),
    path('scans/reports/', get_scans, name='get_scans'),
    path('devices/statuses/', get_device_statuses, name='get_device_statuses'),
    path('devices/<str:mac_address>/status/', update_device_status, name='update_device_status'),
    path('devices/actions/ota/', set_ota_server, name='set_ota_server'),
    path('devices/actions/led/', set_led_color, name='set_led_color'),
    path('devices/actions/network/', connect_network, name='connect_network'),
    path('devices/actions/sleep/', trigger_deep_sleep, name='trigger_deep_sleep'),
    path('devices/actions/streamsettings/', set_stream_settings, name='set_stream_settings'),
]
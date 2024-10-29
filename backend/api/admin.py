from django.contrib import admin
from .models import ScanLog, PingLog, DeviceStatus

admin.site.register(ScanLog)
admin.site.register(PingLog)
admin.site.register(DeviceStatus)
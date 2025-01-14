from django.db import models
from django.utils import timezone

class ScanLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)  # When the scan was started

    def __str__(self):
        return f"Scan at {self.timestamp}"

class PingLog(models.Model):
    scan = models.ForeignKey(ScanLog, on_delete=models.CASCADE, related_name="pings")
    mac_address = models.CharField(max_length=17)
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=100, blank=True)
    version = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)  # Automatically set to ping time

    def __str__(self):
        return f"{self.mac_address} - {self.ip_address} at {self.timestamp}"

class DeviceStatus(models.Model):
    mac_address = models.CharField(max_length=17, unique=True)
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=100, blank=True)
    version = models.CharField(max_length=100, blank=True)
    is_up = models.BooleanField(default=True)  # True if device is up, False if down
    last_seen = models.DateTimeField()  # Last up/down state change timestamp
    initial_uptime = models.DateTimeField(null=True, blank=True)  # When device first went up
    stream_id = models.IntegerField(null=True, blank=True)  # Janus stream ID for this device

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['stream_id'], name='unique_stream_id', condition=models.Q(stream_id__isnull=False)
            ),
        ]

    def __str__(self):
        status = "Up" if self.is_up else "Down"
        return f"{self.mac_address} - {status} since {self.last_seen}"
# backend/api/serializers.py
from rest_framework import serializers
from .models import ScanLog, PingLog, DeviceStatus

class PingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PingLog
        fields = ['mac_address', 'ip_address', 'timestamp', 'location', 'version']

class ScanLogSerializer(serializers.ModelSerializer):
    pings = PingLogSerializer(many=True, read_only=True)

    class Meta:
        model = ScanLog
        fields = ['id', 'timestamp', 'pings']

class DeviceStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceStatus
        exclude = ['id']
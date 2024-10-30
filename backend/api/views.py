# backend/api/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from rest_framework import status
from .models import ScanLog, PingLog, DeviceStatus
from .serializers import ScanLogSerializer, DeviceStatusSerializer

@api_view(['GET'])
def get_scans(request):
    """Retrieve all scan reports, including pings for each scan."""
    scans = ScanLog.objects.all().order_by('-timestamp')
    serializer = ScanLogSerializer(scans, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def create_scan(request):
    """Create a new scan report, logging each device found and updating the status table."""
    devices = request.data.get('devices', [])
    scan = ScanLog.objects.create()

    # Track MAC addresses that are part of the scan
    scanned_mac_addresses = set()

    # Process each device in the scan
    for device in devices:
        mac_address = device.get('mac_address') or device.get('mac')
        ip_address = device.get('ip_address') or device.get('ip')
        location = device.get('location', '')  # Default to empty if location is not provided
        version = device.get('version', '')  # Default to empty if version is not provided

        scanned_mac_addresses.add(mac_address)

        # Create PingLog entries for each device in the scan
        PingLog.objects.create(scan=scan, mac_address=mac_address, ip_address=ip_address, location=location, version=version)

        # Update DeviceStatus table: mark as up if found in scan
        device_status, created = DeviceStatus.objects.get_or_create(
            mac_address=mac_address,
            defaults={
                'ip_address': ip_address,
                'location': location,
                'version': version,
                'is_up': True,
                'initial_uptime': timezone.now(),
                'last_seen': timezone.now(),
            },
        )

        if not created:
            # Update existing device status
            device_status.ip_address = ip_address
            device_status.location = location
            device_status.version = version
            # Only update last_seen if the device is being marked as up
            if not device_status.is_up:
                device_status.initial_uptime = timezone.now()
            device_status.is_up = True
            device_status.last_seen = timezone.now()
            device_status.save()

    # Set to "down" any devices not seen in this scan that were previously "up" without updating last_seen
    DeviceStatus.objects.filter(is_up=True).exclude(mac_address__in=scanned_mac_addresses).update(
        is_up=False, initial_uptime=None
    )

    return Response({"message": "Scan created and statuses updated successfully"}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def get_device_statuses(request):
    """Retrieve the full list of device statuses."""
    statuses = DeviceStatus.objects.all()
    serializer = DeviceStatusSerializer(statuses, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PATCH'])
def update_device_status(request, mac_address):
    """Update the status of a device (up or down) and optionally the location."""
    try:
        device = DeviceStatus.objects.get(mac_address=mac_address)
    except DeviceStatus.DoesNotExist:
        return Response({"error": "Device not found"}, status=status.HTTP_404_NOT_FOUND)

    is_up = request.data.get('is_up')
    location = request.data.get('location')
    version = request.data.get('version')

    # Update the status and location if provided
    if is_up is not None:
        device.is_up = is_up
        device.last_seen = timezone.now()
        if is_up:
            device.initial_uptime = timezone.now() if not device.initial_uptime else device.initial_uptime

    if location is not None:
        device.location = location
    
    if version is not None:
        device.version = version

    device.save()
    return Response({"message": "Device status updated"}, status=status.HTTP_200_OK)
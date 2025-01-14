# backend/api/views.py
import requests
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import ScanLog, PingLog, DeviceStatus
from .serializers import ScanLogSerializer, DeviceStatusSerializer
import requests
import logging
from lighthousenvr import nvr_commands

logger = logging.getLogger(__name__)
NVR_SERVER = "127.0.0.1"
NVR_PORT = 8080
ID_BASE = 6000
ARCHIVE_HOURS = 24
ARCHIVE_SEGMENT_LENGTH = 20


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

    nvr_alive = True
    try:
        nvr_response = requests.get(f"http://{NVR_SERVER}:{NVR_PORT}/api/manage")
        nvr_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to NVR: {e}")
        nvr_alive = False
    nvr_streams = nvr_response.json() if nvr_alive else {}

    stream_ids = {s.get('id'): False for s in nvr_streams.get('streams', []) if s.get('id')}
    db_devices = DeviceStatus.objects.all()
    for device in db_devices:
        if device.stream_id is not None:
            stream_ids[device.stream_id] = False

    found_db_devices = []
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
        found_db_devices.append(device_status)

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

        # Assign a stream ID to the device if it doesn't already have one
        stream_id = device_status.stream_id
        if stream_id is None:
            i = ID_BASE
            while True:
                if stream_ids.get(i) is None:
                    stream_id = i
                    break
                i += 1
            device_status.stream_id = stream_id
            device_status.save()

        # TODO: Add stream to nvr or update it if it already exists
        if nvr_alive:
            try:
                nvr_commands.add_rtsp_stream(
                    nvr_server=NVR_SERVER,
                    name=device_status.location,
                    stream_id=stream_id,
                    url=f"rtsp://{ip_address}:554/",
                    nvr_port=NVR_PORT,
                    description=f"Stream for {device_status.mac_address}",
                    archive_hours=ARCHIVE_HOURS,
                    archive_segment_length=ARCHIVE_SEGMENT_LENGTH,
                )
            except requests.exceptions.RequestException as e:
                logger.error(f"Error adding stream to NVR: {e}")
                pass

        stream_ids[stream_id] = True

    # Disable any streams that were not found in this scan
    for stream_id, found in stream_ids.items():
        if found:
            continue
        device_status = DeviceStatus.objects.filter(stream_id=stream_id).first()
        if device_status is None:
            continue
        device_status.stream_id = None

        try:
            response = nvr_commands.disable_stream(
                nvr_server=NVR_SERVER,
                name=device_status.location,
                nvr_port=NVR_PORT,
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error disabling stream {stream_id}: {e}")
            pass
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

def send_request_to_device(ip_address, endpoint, payload):
    url = f"http://{ip_address}{endpoint}"

    try:
        response = requests.post(url, data=json.dumps(payload), timeout=5)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return {"ip": ip_address, "success": True, "response": response.json()}
    except requests.RequestException as e:
        return {"ip": ip_address, "success": False, "error": str(e)}

@api_view(['POST'])
def set_ota_server(request):
    """Set the OTA server on selected devices."""
    devices = request.data.get('devices', [])
    server = request.data.get('server', '')
    if not server:
        return Response({"error": "OTA server is required"}, status=status.HTTP_400_BAD_REQUEST)

    results = []
    for device in devices:
        ip = device.get('ip_address')
        results.append(send_request_to_device(ip, "/otaserver", {"server": server}))

    return Response({"results": results}, status=status.HTTP_200_OK)

@api_view(['POST'])
def set_led_color(request):
    """Set the LED color on selected devices."""
    devices = request.data.get('devices', [])
    red = request.data.get('red', 0)
    green = request.data.get('green', 0)
    blue = request.data.get('blue', 0)

    results = []
    for device in devices:
        ip = device.get('ip_address')
        results.append(send_request_to_device(ip, "/ledcolor", {"red": red, "green": green, "blue": blue}))

    return Response({"results": results}, status=status.HTTP_200_OK)

@api_view(['POST'])
def connect_network(request):
    """Connect devices to a network."""
    devices = request.data.get('devices', [])
    ssid = request.data.get('ssid', '')
    password = request.data.get('password', '')

    if not ssid or not password:
        return Response({"error": "SSID and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    results = []
    for device in devices:
        ip = device.get('ip_address')
        results.append(send_request_to_device(ip, "/connect", {"ssid": ssid, "password": password}))

    return Response({"results": results}, status=status.HTTP_200_OK)

@api_view(['POST'])
def trigger_deep_sleep(request):
    """Trigger deep sleep mode on selected devices."""
    devices = request.data.get('devices', [])

    results = []
    for device in devices:
        ip = device.get('ip_address')
        results.append(send_request_to_device(ip, "/deepsleep", {}))

    return Response({"results": results}, status=status.HTTP_200_OK)

@api_view(['POST'])
def set_stream_settings(request):
    """Set stream settings on selected devices."""
    devices = request.data.get('devices', [])
    fps = request.data.get('fps', None)
    resolution = request.data.get('resolution', None)
    bitrate = request.data.get('bitrate', None)
    exposureMode = request.data.get('exposureMode', None)
    exposure = request.data.get('exposure', None)
    gain = request.data.get('gain', None)

    results = []
    for device in devices:
        ip = device.get('ip_address')
        payload = {}
        if fps is not None:
            payload['fps'] = fps
        if resolution is not None:
            payload['resolution'] = resolution
        if bitrate is not None:
            payload['bitrate'] = bitrate
        if exposureMode is not None:
            payload['exposureMode'] = exposureMode
        if exposure is not None:
            payload['exposure'] = exposure
        if gain is not None:
            payload['gain'] = gain

        results.append(send_request_to_device(ip, "/setstream", payload))

    return Response({"results": results}, status=status.HTTP_200_OK)
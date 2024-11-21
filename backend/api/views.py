# backend/api/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from rest_framework import status
from .models import ScanLog, PingLog, DeviceStatus
from .serializers import ScanLogSerializer, DeviceStatusSerializer
import requests
import psutil
import logging
import os
import signal

logger = logging.getLogger(__name__)
NVR_SERVER = "127.0.0.1"
ID_BASE = 5000

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

    janus_alive = True
    try:
        janus_response = requests.get(f"http://{NVR_SERVER}:8080/api/manage")
        janus_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Janus: {e}")
        janus_alive = False
    janus_streams = janus_response.json() if janus_alive else {}
    logger.info(f"Janus streams: {janus_streams}")

    # stream_ids = {stream['id']: False for stream in janus_streams.get('streams', [])}
    stream_ids = {s.get('id'): False for s in janus_streams.get('streams', {}) if s.get('id')}
    db_devices = DeviceStatus.objects.all()
    for device in db_devices:
        logger.info(f"Checking stream ID {device.stream_id} for device {device.mac_address}")
        if device.stream_id is not None:
            stream_ids[device.stream_id] = False
    logger.info(f"Stream IDs: {stream_ids}")

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

        # TODO: Add stream to janus or update it if it already exists

        # Start ffmpeg forwarding for the device if it is not already running
        ffmpeg_running = False
        logger.info(f"Checking ffmpeg process for device {device_status.ip_address}, stream ID {device_status.stream_id}, PID {device_status.ffmpeg_pid}")
        if device_status.ffmpeg_pid:
            try:
                p = psutil.Process(device_status.ffmpeg_pid)
                if p.is_running():
                    ffmpeg_running = True
            except psutil.NoSuchProcess:
                pass

        if not ffmpeg_running:
            logger.info(f"Starting ffmpeg forwarding for device {device_status.mac_address}, stream ID {device_status.stream_id}")
            # Start ffmpeg forwarding for the device
            ffmpeg_command = (
                f"ffmpeg -re -rtsp_transport udp -fflags nobuffer -flags low_delay -i "
                f"rtsp://{device_status.ip_address}:554/ -vcodec copy "
                f"-f rtp rtp://{NVR_SERVER}:{device_status.stream_id} > /dev/null 2>&1"
            )
            ffmpeg_process = psutil.Popen(ffmpeg_command, shell=True, preexec_fn=os.setsid)
            device_status.ffmpeg_pid = ffmpeg_process.pid
            device_status.ffmpeg_start_time = timezone.now()
            device_status.save()

        stream_ids[stream_id] = True

        # For Ubivision cameras, add ffmpeg forwarding of the rtsp to udp (probably move this to
        # Ubivision cluster server and have them just give us the udp info)
        # shell: ffmpeg -re -rtsp_transport udp -fflags nobuffer -flags low_delay -i rtsp://192.168.30.81:554/ -vcodec copy -f rtp rtp://vct2-sector6:4444

    

    for id in DeviceStatus.objects.all():
        print(f"Stream ID {id}")
    db_devices = DeviceStatus.objects.all().exclude(id__in=[d.id for d in found_db_devices])
    for device in db_devices:
        logger.info(f"Checking stream ID {device.stream_id} for device {device.mac_address}")
        if device.stream_id is not None:
            stream_ids[device.stream_id] = False

    # Disable ffmpeg forwarding for devices not found in the scan
    print(f"Stream IDs before termination check: {stream_ids}")
    for stream_id, found in stream_ids.items():
        if found:
            continue
        device_status = DeviceStatus.objects.filter(stream_id=stream_id).first()
        if device_status is None:
            continue
        device_status.stream_id = None

        if device_status.ffmpeg_pid is not None:
            try:
                logger.info(f"Terminating ffmpeg process for stream ID {stream_id}")
                # ffmpeg_process = psutil.Process(device_status.ffmpeg_pid)
                # ffmpeg_process.terminate()
                os.killpg(os.getpgid(device_status.ffmpeg_pid), signal.SIGTERM)

            # except psutil.NoSuchProcess:
            #     logger.critical(f"ffmpeg process for stream ID {stream_id} not found")
            #     pass
            except ProcessLookupError:
                logger.critical(f"Process group for PID {device_status.ffmpeg_pid} not found")
            except Exception as e:
                logger.error(f"Error terminating ffmpeg process group: {e}")
            device_status.ffmpeg_pid = None
        device_status.save()

    # TODO: Remove stream from janus if it is no longer needed

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
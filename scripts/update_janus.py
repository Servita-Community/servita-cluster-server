import requests
import json
import time
import argparse
import logging
import subprocess
import signal
import sys

logging.basicConfig(level=logging.INFO)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Network Scanner for detecting devices on a local network."
    )

    parser.add_argument(
        "--api_endpoint",
        type=str,
        default="http://127.0.0.1:8000/api/devices/statuses/",
        help="API endpoint of the cluster server to get device statuses",
    )
    parser.add_argument(
        "--janus_url",
        type=str,
        default="http://127.0.0.1:8088/janus",
        help="Janus HTTP API URL",
    )
    parser.add_argument(
        "--scan_interval", type=int, default=10, help="Time in seconds between scans"
    )

    return parser.parse_args()


def get_devices(api_endpoint):
    try:
        response = requests.get(api_endpoint)
        if response.status_code == 200:
            data = response.json()
            return data
    except (requests.RequestException, json.JSONDecodeError) as e:
        logging.error(f"Error fetching devices: {e}")
    return None


def janus_request(url, data):
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Janus API returned status code {response.status_code}")
    except Exception as e:
        logging.error(f"Exception during Janus API request: {e}")
    return None


def create_janus_session(janus_url):
    data = {"janus": "create", "transaction": "create_session"}
    response = janus_request(janus_url, data)
    if response and response.get("janus") == "success":
        session_id = response["data"]["id"]
        logging.info(f"Created Janus session {session_id}")
        return session_id
    else:
        logging.error("Failed to create Janus session")
        return None


def attach_to_plugin(janus_url, session_id):
    data = {
        "janus": "attach",
        "plugin": "janus.plugin.streaming",
        "transaction": "attach_plugin",
    }
    url = f"{janus_url}/{session_id}"
    response = janus_request(url, data)
    if response and response.get("janus") == "success":
        handle_id = response["data"]["id"]
        logging.info(f"Attached to plugin with handle {handle_id}")
        return handle_id
    else:
        logging.error("Failed to attach to plugin")
        return None


def list_streams(janus_url, session_id, handle_id):
    data = {
        "janus": "message",
        "body": {"request": "list"},
        "transaction": "list_streams",
    }
    url = f"{janus_url}/{session_id}/{handle_id}"
    response = janus_request(url, data)
    if response and response.get("janus") == "success":
        streams = response["plugindata"]["data"]["list"]
        stream_ids = [stream["id"] for stream in streams]
        logging.info(f"Existing streams: {stream_ids}")
        return stream_ids
    else:
        logging.error("Failed to list streams")
        return []


def add_stream(janus_url, session_id, handle_id, stream_config):
    data = {
        "janus": "message",
        "body": {"request": "create", **stream_config},
        "transaction": "add_stream",
    }
    url = f"{janus_url}/{session_id}/{handle_id}"
    response = janus_request(url, data)
    if response and response.get("janus") == "success":
        logging.info(f"Stream {stream_config['id']} added successfully.")
    else:
        logging.error(f"Error adding stream {stream_config['id']}: {response}")


def remove_stream(janus_url, session_id, handle_id, stream_id):
    data = {
        "janus": "message",
        "body": {"request": "destroy", "id": stream_id},
        "transaction": "remove_stream",
    }
    url = f"{janus_url}/{session_id}/{handle_id}"
    response = janus_request(url, data)
    if response and response.get("janus") == "success":
        logging.info(f"Stream {stream_id} removed successfully.")
    else:
        logging.error(f"Error removing stream {stream_id}: {response}")


def update_janus_server(
    on_devices_sorted, janus_url, ffmpeg_processes, first_run=False
):
    logging.info("Updating Janus server...")

    session_id = create_janus_session(janus_url)
    if not session_id:
        return

    handle_id = attach_to_plugin(janus_url, session_id)
    if not handle_id:
        return

    existing_stream_ids = list_streams(janus_url, session_id, handle_id)

    if first_run:
        # Remove all existing streams
        for stream_id in existing_stream_ids:
            remove_stream(janus_url, session_id, handle_id, stream_id)
        existing_stream_ids = []

    desired_streams = {}
    for idx, device in enumerate(on_devices_sorted):
        port = 5000 + idx
        stream_id = port
        desired_streams[stream_id] = {
            "type": "rtp",
            "id": stream_id,
            "description": f"Location: {device['location']}",
            "audio": False,
            "video": True,
            "videoport": port,
            "videopt": 96,
            "videocodec": "H264",
            "secret": "adminpwd",
        }

    # Streams to add and remove
    streams_to_add = set(desired_streams.keys()) - set(existing_stream_ids)
    streams_to_remove = set(existing_stream_ids) - set(desired_streams.keys())

    # Add new streams
    for stream_id in streams_to_add:
        stream_config = desired_streams[stream_id]
        add_stream(janus_url, session_id, handle_id, stream_config)
        # Start ffmpeg process
        device = next(
            (
                d
                for d in on_devices_sorted
                if 5000 + on_devices_sorted.index(d) == stream_id
            ),
            None,
        )
        if device:
            ffmpeg_process = start_ffmpeg_process(device["ip_address"], stream_id)
            ffmpeg_processes[stream_id] = ffmpeg_process

    # Remove old streams
    for stream_id in streams_to_remove:
        remove_stream(janus_url, session_id, handle_id, stream_id)
        # Stop ffmpeg process
        stop_ffmpeg_process(ffmpeg_processes, stream_id)

    # Clean up: detach and destroy session
    detach_from_plugin(janus_url, session_id, handle_id)
    destroy_janus_session(janus_url, session_id)


def start_ffmpeg_process(device_ip, stream_port):
    ffmpeg_command = [
        "ffmpeg",
        "-re",
        "-rtsp_transport",
        "tcp",
        "-i",
        f"rtsp://{device_ip}:554/",
        "-vcodec",
        "copy",
        "-f",
        "rtp",
        f"rtp://127.0.0.1:{stream_port}",
    ]
    logging.info(
        f"Starting ffmpeg process for device {device_ip} on port {stream_port}"
    )
    try:
        process = subprocess.Popen(
            ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return process
    except Exception as e:
        logging.error(f"Failed to start ffmpeg process: {e}")
        return None


def stop_ffmpeg_process(ffmpeg_processes, stream_id):
    process = ffmpeg_processes.get(stream_id)
    if process:
        logging.info(f"Stopping ffmpeg process for stream {stream_id}")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logging.warning(f"ffmpeg process {stream_id} did not terminate, killing it")
            process.kill()
        del ffmpeg_processes[stream_id]
    else:
        logging.warning(f"No ffmpeg process found for stream {stream_id}")


def detach_from_plugin(janus_url, session_id, handle_id):
    data = {
        "janus": "detach",
        "transaction": "detach_plugin",
    }
    url = f"{janus_url}/{session_id}/{handle_id}"
    response = janus_request(url, data)
    if response and response.get("janus") == "success":
        logging.info(f"Detached from plugin handle {handle_id}")
    else:
        logging.error("Failed to detach from plugin")


def destroy_janus_session(janus_url, session_id):
    data = {
        "janus": "destroy",
        "transaction": "destroy_session",
    }
    url = f"{janus_url}/{session_id}"
    response = janus_request(url, data)
    if response and response.get("janus") == "success":
        logging.info(f"Destroyed Janus session {session_id}")
    else:
        logging.error("Failed to destroy Janus session")


def signal_handler(sig, frame):
    logging.info("Interrupt received, shutting down...")
    global ffmpeg_processes
    for stream_id in list(ffmpeg_processes.keys()):
        stop_ffmpeg_process(ffmpeg_processes, stream_id)
    sys.exit(0)


def main():
    args = parse_arguments()
    logging.info(
        f"Starting network scanner with the following configuration:\n"
        f"API Endpoint: {args.api_endpoint}\n"
        f"Janus URL: {args.janus_url}\n"
        f"Scan Interval: {args.scan_interval} seconds\n"
    )

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    previous_device_ids = set()
    global ffmpeg_processes
    ffmpeg_processes = {}  # stream_id: ffmpeg_process

    first_run = True

    while True:
        logging.info("Starting network scan...")
        devices = get_devices(args.api_endpoint)
        if devices is None:
            logging.error("Error getting devices from the cluster server.")
            time.sleep(args.scan_interval)
            continue
        on_devices = [device for device in devices if device["is_up"]]
        logging.info(f"Found {len(on_devices)} devices that are on.")

        on_devices_sorted = sorted(on_devices, key=lambda d: d["mac_address"])
        current_device_ids = set(device["mac_address"] for device in on_devices_sorted)

        if current_device_ids != previous_device_ids or first_run:
            logging.info("Device list has changed. Updating Janus server.")
            update_janus_server(
                on_devices_sorted, args.janus_url, ffmpeg_processes, first_run
            )
            previous_device_ids = current_device_ids
            first_run = False  # Set to False after first run
        else:
            logging.info("No change in device list.")

        time.sleep(args.scan_interval)


if __name__ == "__main__":
    main()

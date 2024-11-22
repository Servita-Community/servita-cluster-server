import requests
import json
import time
import argparse
import logging

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


def update_janus_server(on_devices, janus_url):
    logging.info("Updating Janus server...")

    session_id = create_janus_session(janus_url)
    if not session_id:
        return

    handle_id = attach_to_plugin(janus_url, session_id)
    if not handle_id:
        return

    existing_stream_ids = list_streams(janus_url, session_id, handle_id)

    desired_streams = {}
    for idx, device in enumerate(on_devices):
        stream_id = 5000 + idx
        desired_streams[stream_id] = {
            "type": "rtsp",
            "id": stream_id,
            "description": f"Location: {device['location']}",
            "audio": False,
            "video": True,
            "url": f"rtsp://{device['ip_address']}:554/",
            "secret": "adminpwd",
            "rtsp_reconnect_delay": 5,
            "rtsp_session_timeout": 0,
            "rtsp_timeout": 10,
            "rtsp_conn_timeout": 5,
        }

    # Streams to add and remove
    streams_to_add = set(desired_streams.keys()) - set(existing_stream_ids)
    streams_to_remove = set(existing_stream_ids) - set(desired_streams.keys())

    # Add new streams
    for stream_id in streams_to_add:
        stream_config = desired_streams[stream_id]
        add_stream(janus_url, session_id, handle_id, stream_config)

    # Remove old streams
    for stream_id in streams_to_remove:
        remove_stream(janus_url, session_id, handle_id, stream_id)

    # Clean up: detach and destroy session
    detach_from_plugin(janus_url, session_id, handle_id)
    destroy_janus_session(janus_url, session_id)


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


def main():
    args = parse_arguments()
    logging.info(
        f"Starting network scanner with the following configuration:\n"
        f"API Endpoint: {args.api_endpoint}\n"
        f"Janus URL: {args.janus_url}\n"
        f"Scan Interval: {args.scan_interval} seconds\n"
    )

    previous_device_ids = set()
    while True:
        logging.info("Starting network scan...")
        devices = get_devices(args.api_endpoint)
        if devices is None:
            logging.error("Error getting devices from the cluster server.")
            time.sleep(args.scan_interval)
            continue
        logging.info(f"Found {len(devices)} devices.")
        on_devices = [device for device in devices if device["is_up"]]

        # Extract device IDs (e.g., MAC addresses)
        current_device_ids = set(device["mac_address"] for device in on_devices)

        if current_device_ids != previous_device_ids:
            logging.info("Device list has changed. Updating Janus server.")
            update_janus_server(on_devices, args.janus_url)
            previous_device_ids = current_device_ids
        else:
            logging.info("No change in device list.")

        time.sleep(args.scan_interval)


if __name__ == "__main__":
    main()

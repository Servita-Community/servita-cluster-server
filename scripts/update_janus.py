import requests
import json
import time
import argparse
import logging
import subprocess

logging.basicConfig(level=logging.INFO)


def parse_arguments():
    """Parse command-line arguments for configuration variables."""
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
        "--scan_interval", type=int, default=10, help="Time in seconds between scans"
    )

    return parser.parse_args()


def get_devices(api_endpoint):
    """Get the list of devices from the cluster server."""
    try:
        response = requests.get(api_endpoint)
        if response.status_code == 200:
            data = response.json()
            return data
    except (requests.RequestException, json.JSONDecodeError):
        pass
    return None


def update_janus_server(on_devices):
    """Update the Janus server with the new device status."""
    logging.info("Updating Janus server...")

    # Update the Janus configuration file
    with open("../janus/janus.plugin.streaming.jcfg", "r") as f:
        lines = f.readlines()

    general_idx = next(
        (i for i, line in enumerate(lines) if line.strip() == "general: {"), None
    )
    # Remove existing device entries
    if general_idx is not None:
        closing_brace_idx = next(
            (
                i
                for i, line in enumerate(
                    lines[general_idx + 1 :], start=general_idx + 1
                )
                if line.strip() == "}"
            ),
            None,
        )
        if closing_brace_idx is not None:
            lines = (
                lines[: general_idx + 1]
                + [
                    line
                    for line in lines[general_idx + 1 : closing_brace_idx]
                    if not line.strip().startswith("udp-stream")
                ]
                + lines[closing_brace_idx:]
            )

    # Add new device entries
    ports_to_expose = set()
    new_stream_configs = []
    for idx, device in enumerate(on_devices):
        port = 5000 + idx
        ports_to_expose.add(port)
        stream_config = f"""
udp-stream{idx}: {{
    type = "rtp"
    id = {port}
    description = "Location: {device['location']}, port: {port}"
    audio = false
    video = true
    videoport = {port}
    videopt = 96
    videocodec = "h264"
    secret = "adminpwd"
}}
"""
        new_stream_configs.append(stream_config)

    lines = lines[: general_idx + 1] + new_stream_configs + lines[closing_brace_idx:]

    with open("../janus/janus.plugin.streaming.jcfg", "w") as f:
        f.writelines(lines)

    # Update the Dockerfile
    with open("../janus/Dockerfile", "r") as f:
        lines = f.readlines()
    expose_line_idx = next(
        (i for i, line in enumerate(lines) if line.startswith("EXPOSE ")), None
    )
    if expose_line_idx is not None:
        used_ports = set(map(int, lines[expose_line_idx].split()[1:]))
        lines = lines[:expose_line_idx] + lines[expose_line_idx + 1 :]
    else:
        used_ports = set()
    logging.info(f"Used ports: {used_ports}")

    used_ports.update(ports_to_expose)
    expose_line = f"EXPOSE {' '.join(map(str, sorted(used_ports)))}\n"
    lines.append(expose_line)

    with open("../janus/Dockerfile", "w") as f:
        f.writelines(lines)

    # Restart the Docker container
    try:
        logging.info("Restarting the Docker container to apply changes...")
        subprocess.run(["sudo", "docker", "stop", "ubivision-janus-server"], check=True)
        subprocess.run(["sudo", "docker", "rm", "ubivision-janus-server"], check=True)
        subprocess.run(
            [
                "sudo",
                "docker",
                "run",
                "-d",
                "--name",
                "ubivision-janus-server",
                "--restart",
                "unless-stopped",
                "--network",
                "host",
                "ubivision-janus-image",
                "/opt/janus/bin/janus",
            ],
            check=True,
        )
        logging.info("Docker container restarted successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error restarting Docker container: {e}")


def main():
    """Main loop to continuously scan the network."""
    args = parse_arguments()
    logging.info(
        f"Starting network scanner with the following configuration:\n"
        f"API Endpoint: {args.api_endpoint}\n"
        f"Scan Interval: {args.scan_interval} seconds\n"
    )

    previous_on_devices = []
    while True:
        logging.info("Starting network scan...")
        devices = get_devices(args.api_endpoint)
        if devices is None:
            logging.error("Error getting devices from the cluster server.")
            time.sleep(args.scan_interval)
            continue
        logging.info(f"Found {len(devices)} devices.")
        on_devices = [device for device in devices if device["is_up"]]

        for device in on_devices:
            matching_device = next(
                (
                    d
                    for d in previous_on_devices
                    if d["mac_address"] == device["mac_address"]
                ),
                None,
            )
            if matching_device is None or matching_device["is_up"] != device["is_up"]:
                update_janus_server(on_devices)

        previous_on_devices = on_devices

        time.sleep(args.scan_interval)


if __name__ == "__main__":
    main()

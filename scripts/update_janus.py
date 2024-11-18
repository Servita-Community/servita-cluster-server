import requests
import json
import time
import argparse


def parse_arguments():
    """Parse command-line arguments for configuration variables."""
    parser = argparse.ArgumentParser(description="Network Scanner for detecting devices on a local network.")
    
    parser.add_argument("--api_endpoint", type=str, default="http://127.0.0.1:8000/api/devices/statuses/",
                        help="API endpoint of the cluster server to get device statuses")
    parser.add_argument("--scan_interval", type=int, default=10,
                        help="Time in seconds between scans")
    
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
    print("Updating Janus server...")
    
    with open("../janus/janus.plugin.streaming.jcfg.template", "r") as f:
        lines = f.readlines()
    
    general_idx = next((i for i, line in enumerate(lines) if line.strip() == "general: {"), None)
    # Remove existing device entries
    if general_idx is not None:
        lines = lines[:general_idx + 1] + [line for line in lines[general_idx + 1:] if not line.strip().startswith("udp-stream")]

    # Add new device entries
    ports_to_expose = set()
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
        lines.append(stream_config)

    with open("../janus/janus.plugin.streaming.jcfg", "w") as f:
        f.writelines(lines)
    
    with open("../janus/Dockerfile", "r") as f:
        lines = f.readlines()
    expose_line_idx = next((i for i, line in enumerate(lines) if line.startswith("EXPOSE ")), None)
    if expose_line_idx is not None:
        used_ports = set(map(int, lines[expose_line_idx].split()[1:]))
        lines = lines[:expose_line_idx] + lines[expose_line_idx + 1:]
    else:
        used_ports = set()
    print(f"Used ports: {used_ports}")

    used_ports.update(ports_to_expose)
    expose_line = f"EXPOSE {' '.join(map(str, sorted(used_ports)))}\n"
    lines.append(expose_line)
    
    with open("../janus/Dockerfile", "w") as f:
        f.writelines(lines)

def main():
    """Main loop to continuously scan the network."""
    args = parse_arguments()
    print(f"Starting network scanner with the following configuration:\n"
          f"API Endpoint: {args.api_endpoint}\n"
          f"Scan Interval: {args.scan_interval} seconds\n")

    previous_on_devices = []
    while True:
        print("Starting network scan...")
        devices = get_devices(args.api_endpoint)
        if devices is None:
            print("Error getting devices from the cluster server.")
            time.sleep(args.scan_interval)
        print(f"Found {len(devices)} devices.")
        on_devices = [device for device in devices if device["is_up"]]
        
        for device in on_devices:
            matching_device = next((d for d in previous_on_devices if d["mac_address"] == device["mac_address"]), None)
            if matching_device is None or matching_device["is_up"] != device["is_up"]:
                update_janus_server(on_devices)
        
        previous_on_devices = on_devices
        
        time.sleep(args.scan_interval)

if __name__ == "__main__":
    main()
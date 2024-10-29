import requests
import json
import time
from ipaddress import ip_network
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

def parse_arguments():
    """Parse command-line arguments for configuration variables."""
    parser = argparse.ArgumentParser(description="Network Scanner for detecting devices on a local network.")
    
    parser.add_argument("--api_endpoint", type=str, default="http://127.0.0.1:8000/api/scans/",
                        help="API endpoint to send scan reports to")
    parser.add_argument("--scan_interval", type=int, default=10,
                        help="Time in seconds between scans")
    parser.add_argument("--network_cidr", type=str, default="192.168.1.0/24",
                        help="CIDR of the local network to scan")
    parser.add_argument("--timeout", type=int, default=1,
                        help="Timeout for each device check in seconds")
    parser.add_argument("--workers", type=int, default=20,
                        help="Number of parallel threads for network scanning")
    
    return parser.parse_args()

def is_device_online(ip_address, timeout):
    """Check if the device at the specified IP responds with the expected JSON structure."""
    try:
        response = requests.get(f"http://{ip_address}/status", timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            # Check for required keys in JSON response to confirm device validity
            if all(key in data for key in ["ssid", "ip", "mac"]):
                return data  # Return the JSON data if it matches expected structure
    except (requests.RequestException, json.JSONDecodeError):
        pass
    return None

def check_device(ip, timeout):
    """Check if a single IP address is a valid device and return device info if online."""
    ip_address = str(ip)
    device_data = is_device_online(ip_address, timeout)
    if device_data:
        return {"ssid": device_data["ssid"], "ip_address": device_data["ip"], "mac_address": device_data["mac"]}
    return None

def scan_network(network_cidr, timeout, workers):
    """Scan the network for devices responding with valid JSON structure."""
    devices = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(check_device, ip, timeout): ip for ip in ip_network(network_cidr).hosts()}
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                devices.append(result)

    return devices

def send_scan_report(devices, api_endpoint):
    """Send scan report to the backend API."""
    data = {"devices": devices}
    try:
        response = requests.post(api_endpoint, json=data)
        response.raise_for_status()
        print("Scan report sent successfully.")
    except requests.RequestException as e:
        print(f"Failed to send scan report: {e}")

def main():
    """Main loop to continuously scan the network."""
    args = parse_arguments()
    print(f"Starting network scanner with the following configuration:\n"
          f"API Endpoint: {args.api_endpoint}\n"
          f"Scan Interval: {args.scan_interval} seconds\n"
          f"Network CIDR: {args.network_cidr}\n"
          f"Timeout: {args.timeout} seconds\n"
          f"Workers: {args.workers}")

    while True:
        print("Starting network scan...")
        devices = scan_network(args.network_cidr, args.timeout, args.workers)
        print(f"Found {len(devices)} devices.")
        send_scan_report(devices, args.api_endpoint)
        time.sleep(args.scan_interval)

if __name__ == "__main__":
    main()
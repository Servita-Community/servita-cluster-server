#!/bin/bash

SERVICE_NAME="network_scanner.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
NETWORK_CIDR="192.168.1.0/24"
SCAN_INTERVAL=10
TIMEOUT=1
WORKERS=20
API_ENDPOINT="http://127.0.0.1:8000/api/scans/"

function show_help {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  --api_endpoint       Set the API endpoint for scan reports (default: $API_ENDPOINT)"
  echo "  --scan_interval      Set the scan interval in seconds (default: $SCAN_INTERVAL)"
  echo "  --network_cidr       Set the CIDR for the network to scan (default: $NETWORK_CIDR)"
  echo "  --timeout            Set the timeout for device checks (default: $TIMEOUT)"
  echo "  --workers            Set the number of parallel threads (default: $WORKERS)"
  echo "  --help               Show this help message"
  echo ""
  echo "Example:"
  echo "  sudo ./setup_network_scanner_service.sh --network_cidr 192.168.1.0/24 --scan_interval 15"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --api_endpoint)
      API_ENDPOINT="$2"
      shift # past argument
      shift # past value
      ;;
    --scan_interval)
      SCAN_INTERVAL="$2"
      shift
      shift
      ;;
    --network_cidr)
      NETWORK_CIDR="$2"
      shift
      shift
      ;;
    --timeout)
      TIMEOUT="$2"
      shift
      shift
      ;;
    --workers)
      WORKERS="$2"
      shift
      shift
      ;;
    --help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

# Check if Poetry is accessible by root and install it if necessary
if ! sudo -u root -i poetry --version &> /dev/null; then
  echo "Poetry not found for root. Installing Poetry for root..."
  sudo -u root curl -sSL https://install.python-poetry.org | sudo -u root python3 -
  
  # Add Poetry to PATH in root's .bashrc if not already present
  ROOT_BASHRC="/root/.bashrc"
  POETRY_PATH="/root/.local/bin"
  if ! grep -q "$POETRY_PATH" "$ROOT_BASHRC"; then
    echo "Adding Poetry to PATH in root's .bashrc..."
    echo "export PATH=\"$POETRY_PATH:\$PATH\"" | sudo tee -a "$ROOT_BASHRC" > /dev/null
  fi
  
  # Reload root's .bashrc for current session
  source "$ROOT_BASHRC"
fi

# Use the explicit path to poetry in the service file
POETRY_PATH="/root/.local/bin/poetry"

# Install project dependencies using Poetry as root
echo "Installing project dependencies using Poetry..."
sudo -u root $POETRY_PATH install --no-root

# Define the systemd service content with passed arguments
SERVICE_CONTENT="[Unit]
Description=Network Scanner Service
After=network.target

[Service]
ExecStart=$POETRY_PATH run python3 $(pwd)/scripts/network_scanner.py \\
  --api_endpoint $API_ENDPOINT \\
  --scan_interval $SCAN_INTERVAL \\
  --network_cidr $NETWORK_CIDR \\
  --timeout $TIMEOUT \\
  --workers $WORKERS
WorkingDirectory=$(pwd)
Restart=always
User=$(whoami)
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"

# Create the service file
echo "Creating systemd service file for Network Scanner with the following settings:"
echo "  API Endpoint: $API_ENDPOINT"
echo "  Scan Interval: $SCAN_INTERVAL seconds"
echo "  Network CIDR: $NETWORK_CIDR"
echo "  Timeout: $TIMEOUT seconds"
echo "  Workers: $WORKERS"
echo "$SERVICE_CONTENT" | sudo tee $SERVICE_PATH > /dev/null

# Reload systemd to recognize the new service
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service to start on boot
echo "Enabling $SERVICE_NAME to start on boot..."
sudo systemctl enable $SERVICE_NAME

# Stop the service if it's already running
echo "Stopping $SERVICE_NAME if currently running..."
sudo systemctl stop $SERVICE_NAME

# Start the service to apply the updated Python file
echo "Starting $SERVICE_NAME with updated Python file..."
sudo systemctl start $SERVICE_NAME

echo "Service $SERVICE_NAME setup complete."

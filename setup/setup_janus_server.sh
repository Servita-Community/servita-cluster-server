#!/bin/bash

if [ $# -lt 3 ]; then
    echo "Usage: remote_setup.sh <commit> <user> <janus_server_ip> [target_dir] [--scan-interval <interval>]"
    exit 1
fi

commit=$1
user=$2
host=$3
target_dir="/home/$user/Workspace"
scan_interval=""

shift 3

while [[ $# -gt 0 ]]; do
    case $1 in
        --scan-interval)
            if [ -n "$2" ] && [[ $2 != --* ]]; then
                scan_interval=$2
                shift 2
            else
                scan_interval="10"
                exit 1
            fi
            ;;
        *)
            target_dir=$1
            shift
            ;;
    esac
done

mkdir -p tmp || { echo "Failed to create tmp directory"; exit 1; }

echo "Setting up $host"
ssh "$user@$host" <<EOF
    mkdir -p $target_dir
    cd $target_dir
    if [ ! -d "ubivision-janus" ]; then
        git clone https://github.com/LighthouseAvionics/ubivision-cluster-server.git
    fi
    cd ubivision-cluster-server/janus
    git fetch origin
    git checkout $commit
    sudo docker build -t ubivision-janus-image .
    
    # Check if the container is already running and remove it
    if [ \$(sudo docker ps -a -q -f name=ubivision-janus-server) ]; then
        sudo docker stop ubivision-janus-server
        sudo docker rm ubivision-janus-server
    fi

    sudo docker run -d --name ubivision-janus-server --restart unless-stopped --network host ubivision-janus-image /opt/janus/bin/janus
EOF
if [ $? -ne 0 ]; then
    echo "SSH command failed"
    exit 1
fi

# Check if Poetry is accessible by root and install it if necessary

ssh "$user@$host" <<EOF
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
EOF

# Use the explicit path to poetry in the service file
POETRY_PATH="/root/.local/bin/poetry"

# Install project dependencies using Poetry as root
echo "Installing project dependencies using Poetry..."
ssh "$user@$host" sudo -u root $POETRY_PATH install --no-root

# Define the systemd service content with passed arguments
SERVICE_CONTENT="[Unit]
Description=Network Scanner Service
After=network.target

[Service]
ExecStart=$POETRY_PATH run python3 $target_dir/ubivision-cluster-server/scripts/update_janus.py \\
  --api_endpoint $API_ENDPOINT \\
  --scan_interval $scan_interval \\
WorkingDirectory=$target_dir/ubivision-cluster-server
Restart=always
User=$user
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"

SERVICE_NAME="update-janus"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME.service"

# Create the service file
echo "Creating systemd service file for Network Scanner with the following settings:"
echo "  API Endpoint: $API_ENDPOINT"
echo "  Scan Interval: $SCAN_INTERVAL seconds"
echo "  Network CIDR: $NETWORK_CIDR"
echo "  Timeout: $TIMEOUT seconds"
echo "  Workers: $WORKERS"
ssh "$user@$host" echo "$SERVICE_CONTENT" | sudo tee $SERVICE_PATH > /dev/null

# Reload systemd to recognize the new service
echo "Reloading systemd daemon..."
ssh "$user@$host" sudo systemctl daemon-reload

# Enable the service to start on boot
echo "Enabling $SERVICE_NAME to start on boot..."
ssh "$user@$host" sudo systemctl enable $SERVICE_NAME

# Stop the service if it's already running
echo "Stopping $SERVICE_NAME if currently running..."
ssh "$user@$host" sudo systemctl stop $SERVICE_NAME

# Start the service to apply the updated Python file
echo "Starting $SERVICE_NAME with updated Python file..."
ssh "$user@$host" sudo systemctl start $SERVICE_NAME

echo "Service $SERVICE_NAME setup complete."


echo "Setup complete for $host" > tmp/$host.log

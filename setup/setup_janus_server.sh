#!/bin/bash

if [ $# -lt 5 ]; then
    echo "Usage: remote_setup.sh <commit> <user> <host> <api_ip> <api_port> [--target-dir <dir>] [--scan-interval <interval>]"
    exit 1
fi

commit=$1
user=$2
host=$3
api_ip=$4
api_port=$5
target_dir="/home/$user/Workspace"
scan_interval="10"

shift 5

while [[ $# -gt 0 ]]; do
    case $1 in
        --scan-interval)
            if [ -n "$2" ] && [[ $2 != --* ]]; then
                scan_interval=$2
                shift 2
            else
                echo "Invalid or missing argument for --scan-interval"
                exit 1
            fi
            ;;
        --target-dir)
            if [ -n "$2" ] && [[ $2 != --* ]]; then
                target_dir=$2
                shift 2
            else
                echo "Invalid or missing argument for --target-dir"
                exit 1
            fi
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

mkdir -p tmp || { echo "Failed to create tmp directory"; exit 1; }

echo "Setting up $host"
ssh "$user@$host" <<EOF
    mkdir -p $target_dir
    cd $target_dir
    if [ ! -d "ubivision-cluster-server" ]; then
        git clone https://github.com/LighthouseAvionics/ubivision-cluster-server.git
    fi
    cd $target_dir/ubivision-cluster-server/janus
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

# Install Poetry if not installed
ssh "$user@$host" <<EOF
    if ! command -v poetry &> /dev/null; then
        echo "Poetry not found. Installing Poetry..."
        curl -sSL https://install.python-poetry.org | python3 -
    fi
EOF

# Use the user's Poetry installation
POETRY_PATH="/home/$user/.local/bin/poetry"

# Install project dependencies using Poetry
echo "Installing project dependencies using Poetry..."
ssh "$user@$host" <<EOF
    cd $target_dir/ubivision-cluster-server 
    $POETRY_PATH install
EOF

# Define the systemd service content with passed arguments
SERVICE_CONTENT="[Unit]
Description=Network Scanner Service
After=network.target

[Service]
ExecStart=$POETRY_PATH run python3 $target_dir/ubivision-cluster-server/scripts/update_janus.py \\
  --api_endpoint http://$api_ip:$api_port/api/devices/statuses/ \\
  --scan_interval $scan_interval \\
WorkingDirectory=$target_dir/ubivision-cluster-server/scripts
Environment=$target_dir/ubivision-cluster-server/scripts
Restart=always
User=$user

[Install]
WantedBy=multi-user.target
"

SERVICE_NAME="update-janus"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME.service"

# Create the service file
echo "Creating systemd service file for Network Scanner with the following settings:"
echo "  API Endpoint: http://$api_ip:$api_port/api/devices/statuses/"
echo "  Scan Interval: $scan_interval seconds"
ssh "$user@$host" <<EOF
    echo "$SERVICE_CONTENT" | sudo tee $SERVICE_PATH > /dev/null
EOF

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

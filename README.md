# ubivision-cluster-server
Cluster server Vue/Vuetify frontend and Django REST Python backend code.

## Setting up the backend
1. Install poetry if you haven't already
    ```bash
    pip install poetry
    ``` 
2. Navigate to the project root directory (if not already here)
    ```bash
    cd ubivision-cluster-server
    ```
3. Install backend dependencies
    ```bash
    poetry install
    ```
4.  Migrate the database
    ```bash
    poetry run backend/manage.py migrate
    ```
5.  Run the backend server
    ```bash
    poetry run backend/manage.py runserver 0.0.0.0:8000
    ```
    The backend server should now be running on `http://0.0.0.0:8000`. You can now proceed to setting up the frontend.

## Setting up the frontend
1. Install Node.js and npm

    ```bash
    # installs nvm (Node Version Manager)
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
    # download and install Node.js (you may need to restart the terminal)
    nvm install 22
    # verifies the right Node.js version is in the environment
    node -v # should print `v22.11.0`
    # verifies the right npm version is in the environment
    npm -v # should print `10.9.0`
    ```

2. Install frontend dependencies
   1. Navigate to the frontend directory (Assuming you are in the root directory of the project)
        ```bash
        cd vue-frontend
        ```
    2. Install dependencies
        ```bash
        npm install
        ```

3. Build the frontend
    ```bash
    npm run build
    ```

This will automatically place the built files in the `backend/static` directory. The Django backend will serve the frontend from this directory. Assuming you have already set up the backend and you used port 8000 for the backend, you can now view the frontend by visiting `http://localhost:8000` in your browser.

## Viewing streams in panel view
1. Once your server is running and the frontend is built, use your browser to navigate to `http://localhost:8000/` to view the frontend.
2. Click the `Streams Panel` tab inside the left menu.
   1. If there are cameras on the network and your `network_scanner` service is running, you should see some cameras listed in the expanded panel controls dropdown. 
   2. The cameras are referenced by their location field.
3. Setup the `update-janus` service to run the janus server in the background and allow for streams to be viewed.
   ```bash
   ./setup/setup_janus_server.sh <commit> <user> <host> <api_ip> <api_port> [--target-dir <dir>] [--scan-interval <interval>]
   ```
   - To setup the server on your own computer and on the latest version, use the command:
        ```bash
        ./setup/setup_janus_server.sh $(git rev-parse HEAD) $USER localhost localhost 8000
        ```
4. It may take up to `scan-interval` seconds plus the interval of the `network_scanner` service to see the cameras listed in the panel view. Once this happens, click on any of the cameras in the panel view and then press start to view the streams. 
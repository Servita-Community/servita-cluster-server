# ubivision-cluster-server
Cluster server Vue/Vuetify frontend and Django REST Python backend code.

## Prerequisites
- Python 3.10 or higher
- Node.js 22.x and npm 10.x
- Poetry
- nvm (Node Version Manager)

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
4. Migrate the database
    ```bash
    poetry run backend/manage.py migrate
    ```
5. Run the backend server
    ```bash
    poetry run backend/manage.py runserver 0.0.0.0:8000
    ```
    The backend server should now be running on [http://localhost:8000](http://localhost:8000). You can now proceed to setting up the frontend.

6. The `scripts/network_scanner.py` file can be used to test if the backend is properly setup. 
   1. Open a new terminal window and type the following command to run the network scanner script
        ```bash
        poetry run network_scanner.py -h
        ```
    2. If devices on your network show up as `192.168.1.X` and you setup the backend on `localhost:8000`, you can run the following command to add the devices to the database
        ```bash
        poetry run network_scanner.py
        ```
    3. Otherwise, you can change the network CIDR using:
        ```bash
        poetry run network_scanner.py --network_cidr X.X.X.X/X
        ```
        1. e.g., `poetry run network_scanner.py --network_cidr 192.168.30.0/24`

7. The `network_scanner` service can be set up to scan for cameras on the network and add them to the database in the background. Use the following scripts if you want to not have to run the `network_scanner.py` script manually.
   1. Navigate to the project root directory if not there already `cd ubivision-cluster-server`
   2. Look at the arguments that can be passed to the `setup_network_scan_service.sh` script by running
        ```bash
        ./setup/setup_network_scan_service.sh --help
        ```
   3. To set up with default parameters (assuming you used the same `localhost:8000` setup above), run
        ```bash
        sudo ./setup/setup_network_scan_service.sh
        ```
    4. The script needs to be run with `sudo` to allow the script to properly setup poetry.

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
    npm -v # should print `v10.9.0`
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

This will automatically place the built files in the [static](http://_vscodecontentref_/1) directory. The Django backend will serve the frontend from this directory. Assuming you have already set up the backend and you used port 8000 for the backend, you can now view the frontend by visiting [http://localhost:8000](http://_vscodecontentref_/2) in your browser.

## Setting up streaming
1. Once your server is running and the frontend is built, use your browser to navigate to [http://localhost:8000/](http://_vscodecontentref_/3) to view the frontend.
2. Click the `Streams Panel` tab inside the left menu.
   1. If there are cameras on the network and your `network_scanner` service is running, you should see some cameras listed in the expanded panel controls dropdown. 
   2. The cameras are referenced by their location field.
3. Set up the `update_janus` service to run the Janus server in the background and allow for streams to be viewed.
    ```bash
    ./setup/setup_janus_server.sh <commit> <user> <host> <api_ip> <api_port> [--target-dir <dir>] [--scan-interval <interval>]
    ```
    - To set up the server on your own computer and on the latest version, use the command:
    ```bash
    ./setup/setup_janus_server.sh $(git rev-parse HEAD) $USER localhost localhost 8000
    ```
4. It may take up to `scan-interval` seconds plus the interval of the `network_scanner` service to see the cameras listed in the panel view. Once this happens, click on any of the cameras in the panel view and then press start to view the streams.

## Functionality overview
The frontend gives the user the ability to view and control cameras on the network. The backend provides the API endpoints for the frontend to interact with. The cluster server provides the most high-level functionality of the system. The Fleet Management tab allows for changing multiple cameras at once. If you want to change streams individually, then you can open the top right menu and then click on a cameras (that is on) to view its own frontend with its own controls.

## Making frontend changes
When wanting to update the frontend, it is recommended to run the frontend in `build:watch` mode. To do this, navigate to the `vue-frontend` directory and run the following command:
```bash
npm run build:watch
```
Assuming that you are running the backend, this will automatically rebuild the frontend when changes are made to the frontend code. The Django backend will serve the updated frontend from the `static` directory. This means that you can dynamically see changes made to the frontend by just saving frontend files with changes. This does the same thing as `npm run serve` but it connects to the backend server instead of running a separate server which is useful for development involving API calls.

If you want to build the frontend for production, you can run the following command:
```bash
npm run build
```
This will build the frontend and place the built files in the `static` directory. The Django backend will serve the frontend from this directory. 

#### Creating a new component
To create a new tab in the left menu, create a new file in the `src/components` directory. Then, import the component in the `src/routes.js` file. You can then give it an [mdi-icon](https://pictogrammers.com/library/mdi/) and frontend endpoint (path) as seen below:

```javascript
    { name: 'Fleet Management', path: '/fleetmanagement', component: FleetManagement, icon: 'mdi-truck' },
```

#### Vuetify
To get the elegant styling with few lines of code, [Vuetify Components](https://vuetifyjs.com/en/components/all/#containment) are used in the `<template>` section of the Vue components. These components contain the HTML and CSS styling for the frontend with no need to write CSS. For any component you want to add, there are likely vuetify components that can be used to make the component look good with minimal effort.

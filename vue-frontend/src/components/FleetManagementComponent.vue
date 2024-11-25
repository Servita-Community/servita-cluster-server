<template>
  <v-container>
    <v-row>
      <v-col>
        <v-card>
          <v-card-title
            class="d-flex align-center justify-space-between"
            style="margin-bottom: 0; padding-bottom: 0;"
          >
            <span class="font-weight-bold">Fleet Management</span>
            <v-btn
              color="primary"
              @click="toggleSelectAll"
              class="ml-2"
            >
              {{ isAllSelected ? "Unselect All" : "Select All" }}
            </v-btn>
          </v-card-title>
          <v-data-table
            :items="activeDevicesFormatted"
            class="elevation-1 dense"
          >
            <template v-slot:[`item.Select`]="{ item }">
              <v-checkbox
                v-model="selectedDevicesMap[item['MAC Address']]"
                @change="onCheckboxChange"
                class="justify-start"
              ></v-checkbox>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-card class="mt-4">
          <v-card-title>Device Actions</v-card-title>
          <v-card-text>
            <v-container>

              <!-- OTA Server -->
              <v-row class="align-center">
                <v-col cols="8">
                  <v-text-field
                    v-model="otaServer"
                    label="OTA Server"
                    variant="outlined"
                    clearable
                  ></v-text-field>
                </v-col>
                <v-col cols="4">
                  <v-btn color="primary" block @click="applyOtaServer">
                    Set OTA Server
                  </v-btn>
                </v-col>
              </v-row>


              <v-divider class="my-4"></v-divider>


              <!-- LED Color Picker -->
              <v-row class="align-center">
                <v-col cols="8">
                  <v-color-picker
                    v-model="ledColor"
                    mode="rgb"
                    class="mb-4"
                  ></v-color-picker>
                </v-col>
                <v-col cols="4">
                  <v-btn color="primary" block @click="applyLedColor">
                    Set LED Color
                  </v-btn>
                </v-col>
              </v-row>


              <v-divider class="my-4"></v-divider>


              <!-- Network Settings -->
              <v-row class="align-center">
                <v-col cols="4">
                  <v-text-field
                    v-model="ssid"
                    label="SSID"
                    variant="outlined"
                    clearable
                  ></v-text-field>
                </v-col>
                <v-col cols="4">
                  <v-text-field
                    v-model="password"
                    label="Password"
                    variant="outlined"
                    clearable
                  ></v-text-field>
                </v-col>
                <v-col cols="4">
                  <v-btn color="primary" block @click="applyNetworkSettings">
                    Connect to Network
                  </v-btn>
                </v-col>
              </v-row>


              <v-divider class="my-4"></v-divider>

              <v-container class="d-flex align-center justify-center" style="gap: 16px;">
                <v-text-field
                  v-model="fps"
                  label="FPS"
                  hint="Between 1 & 30"
                  variant="outlined"
                  clearable
                ></v-text-field>
                <v-select
                  v-model="resolution"
                  :items="resolutions"
                  label="Resolution"
                  variant="outlined"
                  clearable
                ></v-select>
                <v-text-field
                  v-model="bitrate"
                  label="Bitrate (bps)"
                  hint="<= 4194304"
                  variant="outlined"
                  clearable
                ></v-text-field>
              </v-container>

              <v-container class="d-flex align-center justify-center" style="gap: 16px;">
                <v-select
                  v-model="exposureMode"
                  :items="exposureModes"
                  label="Exposure Mode"
                  variant="outlined"
                  clearable
                ></v-select>
                <v-text-field
                  v-model="exposure"
                  label="Exposure (μs)"
                  hint="<= 33333 μs"
                  variant="outlined"
                  clearable
                ></v-text-field>
              </v-container>

              <v-container class="d-flex align-center justify-center" style="gap: 16px;">
                <v-text-field
                  v-model="gain"
                  label="Auto Exposure Gain"
                  hint="Between 256 & 32768"
                  variant="outlined"
                  clearable
                ></v-text-field>
              </v-container>
              <v-btn block color="primary" class="mt-4" @click="applyStreamSettings">
                Set Stream Settings
              </v-btn>


              <v-divider class="my-4"></v-divider>


              <!-- Deep Sleep -->
              <v-row class="align-center">
                <v-col>
                  <v-btn
                    color="red darken-3"
                    class="white--text"
                    block
                    @click="applyDeepSleep"
                  >
                    Enter Deep Sleep
                  </v-btn>
                </v-col>
              </v-row>


            </v-container>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import axios from "axios";

// Device Management State
const devices = ref([]);
const otaServer = ref("");
const ledColor = ref({ r: 255, g: 255, b: 255 });
const ssid = ref("");
const password = ref("");

const fps = ref(null);
const resolution = ref(null);
const bitrate = ref(null);
const exposureMode = ref(null);
const exposure = ref(null);
const gain = ref(null);

const resolutions = ref(['1920x1080', '1280x720', '640x480']); // Add your desired resolutions here
const exposureModes = ref(['Auto', 'Manual']); // Add your desired exposure modes here

const baseUrl = `${window.location.origin}/api/devices/statuses/`;

async function fetchDeviceStatuses() {
  try {
    const response = await axios.get(baseUrl);
    devices.value = response.data.map((device) => ({
      select: device.mac_address,
      macAddress: device.mac_address,
      ipAddress: device.ip_address,
      location: device.location || "Unknown",
      version: device.version,
      uptime: calculateUptime(device.initial_uptime),
      isUp: device.is_up,
    }));
  } catch (error) {
    console.error("Error fetching device statuses:", error);
  }
}

function calculateUptime(initialUptime) {
  const uptimeDuration = Math.floor((new Date() - new Date(initialUptime)) / 1000);
  return formatDuration(uptimeDuration);
}

function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${hours}h ${minutes}m ${secs}s`;
}

// Formatted Active Devices
const activeDevicesFormatted = computed(() =>
  devices.value.filter((device) => device.isUp).map((device) => ({
    Select: device.macAddress,
    "MAC Address": device.macAddress,
    "IP Address": device.ipAddress,
    Firmware: device.version,
    Location: device.location,
    Uptime: device.uptime,
  }))
);

const selectedDevicesMap = ref({});

// Watch Selected Devices
watch(
  activeDevicesFormatted,
  (newDevices) => {
    const newMap = {};
    newDevices.forEach((device) => {
      newMap[device["MAC Address"]] = selectedDevicesMap.value[device["MAC Address"]] || false;
    });
    selectedDevicesMap.value = newMap;
  },
  { immediate: true, deep: true }
);

const selectedDevices = computed(() =>
  activeDevicesFormatted.value.filter((device) => selectedDevicesMap.value[device["MAC Address"]])
);

const isAllSelected = computed(() =>
  activeDevicesFormatted.value.length > 0 &&
  activeDevicesFormatted.value.every((device) => selectedDevicesMap.value[device["MAC Address"]])
);

function toggleSelectAll() {
  const selectAll = !isAllSelected.value;
  activeDevicesFormatted.value.forEach((device) => {
    selectedDevicesMap.value[device["MAC Address"]] = selectAll;
  });
}

async function applyOtaServer() {
  const payload = {
    devices: selectedDevices.value.map(device => ({ ip_address: device["IP Address"] })),
    server: otaServer.value,
  };
  await applyToBackend("/api/devices/actions/ota/", payload);
}

async function applyLedColor() {
  const payload = {
    devices: selectedDevices.value.map(device => ({ ip_address: device["IP Address"] })),
    red: ledColor.value.r,
    green: ledColor.value.g,
    blue: ledColor.value.b,
  };
  await applyToBackend("/api/devices/actions/led/", payload);
}

async function applyNetworkSettings() {
  const payload = {
    devices: selectedDevices.value.map(device => ({ ip_address: device["IP Address"] })),
    ssid: ssid.value,
    password: password.value,
  };
  await applyToBackend("/api/devices/actions/network/", payload);
}

async function applyDeepSleep() {
  const payload = {
    devices: selectedDevices.value.map(device => ({ ip_address: device["IP Address"] })),
  };
  await applyToBackend("/api/devices/actions/sleep/", payload);
}

async function applyStreamSettings() {

  const payload = {
    devices: selectedDevices.value.map(device => ({ ip_address: device["IP Address"] })),
  }

  if (fps.value) payload.fps = fps.value;
  if (resolution.value) payload.resolution = resolution.value;
  if (bitrate.value) payload.bitrate = bitrate.value;
  if (exposureMode.value) payload.exposureMode = exposureMode.value;
  if (exposure.value) payload.exposure = exposure.value;
  if (gain.value) payload.gain = gain.value;

  await applyToBackend("/api/devices/actions/streamsettings/", payload);
}

async function applyToBackend(url, payload) {
  try {
    const response = await axios.post(url, payload);
    console.log("Action applied successfully:", response.data);
  } catch (error) {
    console.error("Failed to apply action:", error);
  }
}

onMounted(() => {
  fetchDeviceStatuses();
  setInterval(fetchDeviceStatuses, 10000);
});
</script>
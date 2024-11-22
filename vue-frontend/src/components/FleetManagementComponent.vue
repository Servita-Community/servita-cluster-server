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
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import axios from "axios";

// Raw devices data
const devices = ref([]);

// Fetch device statuses from API
const baseUrl = `${window.location.origin}/api/devices/statuses/`;

async function fetchDeviceStatuses() {
  try {
    const response = await axios.get(baseUrl);
    devices.value = response.data.map((device) => ({
      select: device.mac_address, // Unique identifier for checkbox selection
      ipAddress: device.ip_address,
      macAddress: device.mac_address,
      location: device.location || "Unknown",
      uptime: calculateUptime(device.initial_uptime),
      downtime: calculateDowntime(device.last_seen),
      version: device.version,
      isUp: device.is_up,
    }));
  } catch (error) {
    console.error("Error fetching device statuses:", error);
  }
}

// Helper functions
function calculateUptime(initialUptime) {
  const uptimeDuration = Math.floor((new Date() - new Date(initialUptime)) / 1000);
  return formatDuration(uptimeDuration);
}

function calculateDowntime(lastSeen) {
  const downtimeDuration = Math.floor((new Date() - new Date(lastSeen)) / 1000);
  return formatDuration(downtimeDuration);
}

function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${hours}h ${minutes}m ${secs}s`;
}

// Filter active devices and format them for the table
const activeDevicesFormatted = computed(() =>
  devices.value
    .filter((device) => device.isUp) // Only include active devices
    .map((device) => ({
      Select: device.macAddress, // Unique identifier for selection
      "MAC Address": device.macAddress,
      "IP Address": device.ipAddress,
      Firmware: device.version,
      Location: device.location,
      Uptime: device.uptime,
    }))
);

// Selected devices map
const selectedDevicesMap = ref({});

// Update selection map whenever devices change
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

// Computed property for selected devices
const selectedDevices = computed(() =>
  activeDevicesFormatted.value.filter((device) => selectedDevicesMap.value[device["MAC Address"]])
);

// Check if all devices are selected
const isAllSelected = computed(() => 
  activeDevicesFormatted.value.length > 0 &&
  activeDevicesFormatted.value.every((device) => selectedDevicesMap.value[device["MAC Address"]])
);

// Toggle all devices' selection state
function toggleSelectAll() {
  const selectAll = !isAllSelected.value;
  activeDevicesFormatted.value.forEach((device) => {
    selectedDevicesMap.value[device["MAC Address"]] = selectAll;
  });
}

// Handle checkbox change
function onCheckboxChange() {
  console.log("Selected devices:", selectedDevices.value);
}

// Periodic refresh
let intervalId;
onMounted(() => {
  fetchDeviceStatuses();
  intervalId = setInterval(fetchDeviceStatuses, 10000);
});

onUnmounted(() => {
  clearInterval(intervalId);
});
</script>
<template>
  <v-container fluid>
    <v-app-bar app>
      <v-app-bar-nav-icon @click="leftDrawer = !leftDrawer" class="d-flex align-center"></v-app-bar-nav-icon>
      <v-spacer />
      <v-img 
        src="../../public/ubihere.webp" 
        class="logo" 
        width="auto" 
        @click="$router.replace('/')"
        style="cursor: pointer;"
      ></v-img>
      <v-spacer />
      <v-app-bar-nav-icon @click="rightDrawer = !rightDrawer" class="d-flex align-center">
        <v-icon>mdi-camera</v-icon>
      </v-app-bar-nav-icon>
    </v-app-bar>
    <v-navigation-drawer app v-model="leftDrawer">
      <v-list>
        <router-link
          v-for="route in routes.filter(route => route.path !== '/')"
          :key="route.path"
          :to="route.path"
          style="text-decoration: none; color: inherit;"
        >
          <v-list-item link>
            <template v-slot:prepend>
              <v-icon>{{ route.icon }}</v-icon>
            </template>
            <v-list-item-title v-text="route.name"></v-list-item-title>
          </v-list-item>
        </router-link>
      </v-list>
    </v-navigation-drawer>

    <!-- Right Drawer for Device Statuses -->
    <v-navigation-drawer app v-model="rightDrawer" temporary location="right">
      <v-list>
        <v-list-item
          v-for="device in sortedDevices"
          :key="device.mac_address"
          :href="'http://' + device.ip_address"
          target="_blank"
          style="text-decoration: none; color: inherit;"
        >
          <template v-slot:prepend>
            <v-icon :color="device.is_up ? 'green' : 'red'">mdi-circle</v-icon>
          </template>
          <v-list-item-content>
            <v-list-item-title>{{ device.ip_address }}</v-list-item-title>
            <v-list-item-subtitle>MAC: {{ device.mac_address }}</v-list-item-subtitle>
            <v-list-item-subtitle>
              {{ device.is_up ? 'Uptime: ' + device.uptime : 'Downtime: ' + device.downtime }}
            </v-list-item-subtitle>
            <v-list-item-subtitle v-if="device.location && device.location.length > 0">
              Location: {{ device.location }}
            </v-list-item-subtitle>
            <v-list-item-subtitle v-if="device.version && device.version.length > 0">
              Firmware: {{ device.version }}
            </v-list-item-subtitle>
          </v-list-item-content>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import routes from '../routes'

const leftDrawer = ref(false)
const rightDrawer = ref(false)
const devices = ref([])

const baseUrl = `${window.location.origin}/api/devices/statuses/`

async function fetchDeviceStatuses() {
  try {
    const response = await axios.get(baseUrl)
    devices.value = response.data.map(device => ({
      ...device,
      uptime: calculateUptime(device.initial_uptime),
      downtime: calculateDowntime(device.last_seen),
    }))
  } catch (error) {
    console.error('Error fetching device statuses:', error)
  }
}

function calculateUptime(initialUptime) {
  const uptimeDuration = Math.floor((new Date() - new Date(initialUptime)) / 1000)
  return formatDuration(uptimeDuration)
}

function calculateDowntime(lastSeen) {
  const downtimeDuration = Math.floor((new Date() - new Date(lastSeen)) / 1000)
  return formatDuration(downtimeDuration)
}

function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  return `${hours}h ${minutes}m ${secs}s`
}

// Computed property to sort devices
const sortedDevices = computed(() => {
  const activeDevices = devices.value
    .filter(device => device.is_up)
    .sort((a, b) => new Date(b.initial_uptime) - new Date(a.initial_uptime)) // Most recently active first
  const inactiveDevices = devices.value
    .filter(device => !device.is_up)
    .sort((a, b) => new Date(b.last_seen) - new Date(a.last_seen)) // Most recently inactive first
  return [...activeDevices, ...inactiveDevices]
})

// Refresh device statuses every 10 seconds
let intervalId
onMounted(() => {
  fetchDeviceStatuses()
  intervalId = setInterval(fetchDeviceStatuses, 10000)
})

onUnmounted(() => {
  clearInterval(intervalId)
})
</script>

<style scoped>
.logo {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}
</style>
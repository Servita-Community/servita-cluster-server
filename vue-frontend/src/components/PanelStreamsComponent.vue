<template>
  <v-container fluid>

    <!-- Stream Select Controls -->
    <v-card justify="center" :style="{ maxWidth: '600px' }" class="mx-auto">
      <v-card-title class="text-center text-h6">
        Stream Page
      </v-card-title>
      <v-card-text class="text-center">
        <v-card-actions class="d-flex justify-center">
          <v-btn :color="isLedOn ? 'green' : isLoading ? 'blue' : 'red'" class="mr-2">
            <v-icon v-if="isLedOn">mdi-led-on</v-icon>
            <v-icon v-else-if="isLoading" class="mdi-spin">mdi-loading</v-icon>
            <v-icon v-else>mdi-led-off</v-icon>
            <span v-if="isLedOn">Streaming</span>
            <span v-else-if="isLoading">Loading...</span>
            <span v-else>Stream Off</span>
          </v-btn>
          <v-btn color="primary" @click="toggleStream">
            {{ isStreaming ? 'Stop Stream' : 'Start Stream' }}
          </v-btn>
        </v-card-actions>
      </v-card-text>
      <v-card-actions class="d-flex justify-center">
        <v-select
          v-model="selectedStream"
          :items="streams"
          item-title="location"
          item-value="mac_address"
          label="Select Stream"
          outlined
        ></v-select>
      </v-card-actions>
    </v-card>

    <v-divider class="my-8" />

    <!-- 4-Stream Video Panel -->
    <v-container fluid>
      <v-row>
        <v-col cols="6" v-for="(stream, index) in filteredStreams" :key="stream.mac_address">
          <v-card>
            <v-card-title class="text-center">Location - {{ stream.location }}</v-card-title>
            <v-card-text>
              <video
                v-if="isStreaming && selectedStream === stream.mac_address"
                :id="`video${index}`"
                autoplay
                controls
                style="width: 100%; height: auto;"
              ></video>
              <div v-else class="text-center">
                Select a stream to view
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { Janus } from 'janus-gateway'

const isLedOn = ref(false)
const isStreaming = ref(false)
const isLoading = ref(false)
const selectedStream = ref(null)
const streams = ref([]) // Array of devices fetched from the backend
const janus = ref(null)
const pluginHandles = ref([]) // Store plugin handles for each Janus stream
const janusRunning = ref(false)

// Fetch streams from API
const fetchStreams = async () => {
  try {
    const response = await axios.get(`http://${window.location.hostname}:${window.location.port}/api/devices/statuses/`)
    streams.value = response.data.filter(device => device.is_up && device.ip_address).map(device => ({
      mac_address: device.mac_address,
      ip_address: device.ip_address,
      location: device.location,
      last_seen: device.last_seen,
    }))
  } catch (error) {
    console.error('Failed to fetch device statuses:', error)
  }
}

// Limit to 4 streams for display
const filteredStreams = computed(() => streams.value.slice(0, 4))

// Initialize Janus
const startJanus = () => {
  Janus.init({
    debug: 'all',
    dependencies: Janus.useDefaultDependencies(),
    callback: createSession,
  })
}

// Create a new Janus session
const createSession = () => {
  janus.value = new Janus({
    server: 'ws://heimdall-64gb-14.local:8188/', // Replace with your Janus server
    success: attachPlugins,
    error: (error) => console.error('Error creating Janus session:', error),
    destroyed: () => console.log('Janus session destroyed'),
  })
}

// Attach plugins for each stream
const attachPlugins = () => {
  const streamIds = [5002, 5000, 5001, 5003] // Replace with the actual stream IDs from Janus

  streamIds.forEach((streamId, index) => {
    janus.value.attach({
      plugin: 'janus.plugin.streaming',
      success: (handle) => {
        pluginHandles.value[index] = handle
        console.log('Plugin attached:', handle)
        pluginHandles.value[index].send({ message: { request: 'watch', id: streamId } })
        janusRunning.value = true
      },
      error: (error) => console.error('Error attaching plugin:', error),
      onmessage: (_msg, jsep) => {
        if (jsep) {
          pluginHandles.value[index].createAnswer({
            jsep: jsep,
            media: { audioSend: false, videoSend: false },
            success: (ourJsep) => {
              pluginHandles.value[index].send({ message: { request: 'start' }, jsep: ourJsep })
            },
            error: (error) => console.error('WebRTC error:', error),
          })
        }
      },
      onremotetrack: (track, _mid, added) => {
        if (track.kind === 'video' && added) {
          const videoElement = document.getElementById(`video${index}`)
          if (videoElement) {
            const stream = new MediaStream()
            stream.addTrack(track.clone())
            videoElement.srcObject = stream
          } else {
            console.error(`Video element with id video${index} not found`)
          }
        }
      },
      oncleanup: () => console.log('Plugin cleaned up'),
    })
  })
}

// Start or stop streaming
const toggleStream = async () => {
  if (isStreaming.value) {
    stopJanus()
    isStreaming.value = false
    isLedOn.value = false
  } else {
    isLoading.value = true
    try {
      await new Promise(resolve => setTimeout(resolve, 2000)) // Simulate delay
      if (selectedStream.value) {
        startJanus()
        isStreaming.value = true
        isLedOn.value = true
      } else {
        console.error('No stream selected or invalid stream')
      }
    } catch (error) {
      console.error('Failed to start the streams:', error)
    } finally {
      isLoading.value = false
    }
  }
}

// Stop Janus and detach plugins
const stopJanus = () => {
  pluginHandles.value.forEach(handle => {
    if (handle) {
      handle.hangup()
      handle.detach()
    }
  })
  pluginHandles.value = []

  if (janus.value) {
    janus.value.destroy()
    janus.value = null
  }

  janusRunning.value = false
}

// Fetch streams on component mount
onMounted(fetchStreams)
</script>

<style scoped>
</style>
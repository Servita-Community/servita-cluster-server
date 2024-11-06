<template>
  <v-container fluid>
    <!-- Stream Select Controls -->
    <v-expansion-panels>
      <v-expansion-panel title="Panel Controls" justify="center" :style="{ maxWidth: '600px' }" class="mx-auto">
        <v-expansion-panel-text>
          <v-card flat :loading="isLoading" justify="center" :style="{ maxWidth: '600px' }" class="mx-auto">
            <v-card-text class="text-center pt-6">
              <v-card-actions class="d-flex justify-center">
                <v-slider v-model="streamSize" :max="6" :min="1" :step="1" thumb-label="always" class="mr-2" hide-details />
                <v-divider vertical class="mx-2"></v-divider>
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
              <v-responsive class="overflow-y-auto" max-height="280">
                <v-chip-group multiple column>
                  <v-chip
                    v-for="stream in streams"
                    :key="stream.mac_address"
                    :color="selectedStreams.includes(stream.mac_address) ? 'info' : 'grey'"
                    @click="toggleSelectedStream(stream.mac_address)"
                  >
                    {{ stream.location }}
                  </v-chip>
                </v-chip-group>
              </v-responsive>
            </v-card-actions>
          </v-card>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <v-divider class="mt-4" />

    <!-- Stream Video Display -->
    <v-container fluid>
      <v-row dense>
        <v-col 
          :cols="enlargedStreamIndex === index ? streamSize * 2 : streamSize" 
          v-for="(stream, index) in filteredStreams" 
          :key="stream.mac_address"
          class="transition-col"
        >
          <v-tooltip :text="stream.location">
            <template v-slot:activator="{ props }">
              <v-card
                v-if="isStreaming && selectedStreams.includes(stream.mac_address)"
                dense
                v-bind="props"
                class="pa-1"
                :class="{ 'enlarged-stream': enlargedStreamIndex === index }"
                @click="toggleEnlargeStream(index)"
              >
                <v-card-text class="pa-1">
                  <video
                    v-if="isStreaming && selectedStreams.includes(stream.mac_address)"
                    :id="`video${index}`"
                    autoplay
                    controls
                    style="width: 100%; height: auto;"
                  ></video>
                </v-card-text>
              </v-card>
            </template>
          </v-tooltip>
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
const selectedStreams = ref([]) // Array to hold selected streams
const streamSize = ref(3) // Number of streams to display
const streams = ref([]) // Array of devices fetched from the backend
const janus = ref(null)
const pluginHandles = ref([]) // Store plugin handles for each Janus stream
const janusRunning = ref(false)
const enlargedStreamIndex = ref(null) // Index of the stream to enlarge

// Toggle selection for a stream
const toggleSelectedStream = (macAddress) => {
  const index = selectedStreams.value.indexOf(macAddress)
  if (index === -1) {
    selectedStreams.value.push(macAddress)
    if (isStreaming.value) {
      stopJanus()
      startJanus()
    }
  } else {
    selectedStreams.value.splice(index, 1)
  }
}

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

// Attach plugins for each selected stream
const attachPlugins = () => {
  const streamIds = [5002, 5000, 5001, 5003] // Replace with actual stream IDs for each selected stream

  selectedStreams.value.forEach((_, index) => {
    const streamId = streamIds[index % streamIds.length] // Adjust stream IDs as necessary

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

// Start or stop streaming for all selected streams
const toggleStream = async () => {
  if (isStreaming.value) {
    stopJanus()
    isStreaming.value = false
    isLedOn.value = false
  } else {
    isLoading.value = true
    try {
      await new Promise(resolve => setTimeout(resolve, 2000)) // Simulate delay
      if (selectedStreams.value.length > 0) {
        startJanus()
        isStreaming.value = true
        isLedOn.value = true
      } else {
        console.error('No streams selected')
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

// Toggle enlarged stream view
const toggleEnlargeStream = (index) => {
  enlargedStreamIndex.value = enlargedStreamIndex.value === index ? null : index
}

onMounted(fetchStreams)
</script>

<style scoped>
.enlarged-stream {
  transition: all 0.3s ease;
  transform: scale(1.5); /* Adjust the scaling to make it larger */
  z-index: 10;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
}
.transition-col {
  transition: width 0.3s ease;
}
</style>

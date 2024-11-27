<template>
  <v-container fluid>
    <!-- Stream Select Controls -->
    <v-expansion-panels>
      <v-expansion-panel title="Panel Controls" :style="{ maxWidth: '600px' }" class="mx-auto">
        <v-expansion-panel-text>
          <v-card flat :loading="isLoading" justify="center" :style="{ maxWidth: '600px' }" class="mx-auto">
            <v-card-text class="text-center pt-8">
              <v-card-actions class="d-flex justify-center">
                <v-slider v-model="streamSize" :max="6" :min="1" :step="1" thumb-label="always" class="mr-2" :style="{minWidth: '100px'}" hide-details />
                <v-divider vertical class="mx-2"></v-divider>
                <v-btn :color="isLedOn ? 'green' : isLoading ? 'blue' : 'red'" class="mr-2">
                  <v-icon v-if="isLedOn">mdi-led-on</v-icon>
                  <v-icon v-else-if="isLoading" class="mdi-spin">mdi-loading</v-icon>
                  <v-icon v-else>mdi-led-off</v-icon>
                  <span v-if="isLedOn">Good</span>
                  <span v-else-if="isLoading" />
                  <span v-else>Off</span>
                </v-btn>
                <v-btn color="primary" @click="toggleStream">
                  {{ isStreaming ? 'Stop' : 'Start' }}
                </v-btn>
              </v-card-actions>
            </v-card-text>
            <v-card-actions class="d-flex justify-center">
              <v-responsive class="overflow-y-auto" max-height="280">
                <v-chip-group multiple column>
                  <v-chip
                    v-for="stream in streams"
                    :key="stream.mac_address"
                    @click="toggleSelectedStream(stream.mac_address)"
                    :class="{ 'selected-chip': selectedStreams.includes(stream.mac_address) }"
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

    <v-divider class="my-4" />

    <!-- Stream Video Display -->
    <v-row dense>
      <transition-group name="fade">
        <v-col
          v-for="(stream, index) in streams.filter(s => selectedStreams.includes(s.mac_address))"
          :key="stream.mac_address"
          :cols="enlargedStreamIndex === index ? '6' : streamSize"
          :style="{ transition: 'all 0.3s ease' }"
        >
          <v-tooltip :text="stream.location">
            <template v-slot:activator="{ props }">
              <v-card
                v-if="isStreaming && selectedStreams.includes(stream.mac_address)"
                v-bind="props"
                dense
                class="pa-1"
                @click="toggleEnlargeStream(index)"
              >
                <v-card-text class="pa-1 text-centered">
                  <video
                    :id="`video-${stream.mac_address}`"
                    autoplay
                    controls
                    width="100%"
                    height="100%"
                  ></video>
                </v-card-text>
              </v-card>
            </template>
          </v-tooltip>
        </v-col>
      </transition-group>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { Janus } from 'janus-gateway';

const isLedOn = ref(false);
const isStreaming = ref(false);
const isLoading = ref(false);
const selectedStreams = ref([]); // Array of selected stream MAC addresses
const streamSize = ref(3); // Number of streams to display
const streams = ref([]); // Array of devices fetched from the backend
const janus = ref(null);
const pluginHandles = ref([]); // Store plugin handles for each Janus stream
const janusStreamMap = ref({}); // Map from location to stream ID
const enlargedStreamIndex = ref(null); // Index of the stream to enlarge

// Update aspect ratio when a stream is clicked
const toggleEnlargeStream = (index) => {
  enlargedStreamIndex.value = enlargedStreamIndex.value === index ? null : index;
};

// Toggle selection for a stream
const toggleSelectedStream = (macAddress) => {
  const index = selectedStreams.value.indexOf(macAddress);
  if (index === -1) {
    selectedStreams.value.push(macAddress);
    if (isStreaming.value) {
      // Restart Janus to include new stream
      stopJanus();
      startJanus();
    }
  } else {
    selectedStreams.value.splice(index, 1);
    if (isStreaming.value) {
      // Restart Janus without the removed stream
      stopJanus();
      startJanus();
    }
  }
};

// Fetch streams from API
const fetchStreams = async () => {
  try {
    const response = await axios.get(`http://${window.location.hostname}:${window.location.port}/api/devices/statuses/`);
    streams.value = response.data.filter(device => device.is_up && device.ip_address).map(device => ({
      mac_address: device.mac_address,
      ip_address: device.ip_address,
      location: device.location,
      last_seen: device.last_seen,
    }));
  } catch (error) {
    console.error('Failed to fetch device statuses:', error);
  }
};

// Initialize Janus
const startJanus = () => {
  if (!Janus.isWebrtcSupported()) {
    console.error('No WebRTC support... ');
    return;
  } else {
    Janus.init({
      debug: 'all',
      dependencies: Janus.useDefaultDependencies(),
      callback: createSession,
    })
  }
};

const createSession = () => {
  janus.value = new Janus({
    server: `ws://${window.location.hostname}:8188/`,
    success: () => {
      console.log('Janus session established');
      fetchStreamIds();
    },
    error: (cause) => {
      console.error('Error creating Janus session', cause);
      // Attempt to reconnect after a delay
      setTimeout(() => {
        console.log('Attempting to reconnect to Janus server...');
        createSession();
      }, 2000); // Retry after 2 seconds
    },
    destroyed: () => {
      console.log('Janus session destroyed');
      // Attempt to recreate the session
      setTimeout(() => {
        console.log('Recreating Janus session...');
        createSession();
      }, 2000);
    },
  });
};

// Fetch available stream IDs from the Janus server
const fetchStreamIds = () => {
  janus.value.attach({
    plugin: 'janus.plugin.streaming',
    success: (pluginHandle) => {
      pluginHandle.send({
        message: { request: 'list' },
        success: (response) => {
          const streamsData = response.list || [];
          console.log('Available Streams:', response);

          // Build a mapping from location to stream ID
          const streamMap = {};
          streamsData.forEach((stream) => {
            // Parse location from description
            // Assuming description is "Location: Some Location, port: 5000"
            const description = stream.description || '';
            const locationMatch = description.match(/Location:\s*([^,]+)/);
            if (locationMatch) {
              const streamLocation = locationMatch[1];
              streamMap[streamLocation] = stream.id;
              console.log('Janus stream location:', streamLocation);
              console.log('StreamMap:', streamMap);
            }
          });

          janusStreamMap.value = streamMap;

          // Proceed to attach plugins
          attachPlugins();
        },
        error: (error) => {
          console.error('Error fetching streams:', error);
          // Attempt to refetch after a delay
          setTimeout(fetchStreamIds, 2000);
        },
      });
    },
    error: (error) => {
      console.error('Error attaching streaming plugin:', error);
      // Attempt to reattach after a delay
      setTimeout(fetchStreamIds, 2000);
    },
  });
};

// Attach plugins for each selected stream
const attachPlugins = () => {
  pluginHandles.value = {}; // Use an object for plugin handles
  selectedStreams.value.forEach((macAddress) => {
    const stream = streams.value.find(s => s.mac_address === macAddress);
    if (!stream) {
      console.error(`No stream found for MAC address ${macAddress}`);
      return;
    }
    const deviceLocation = stream.location;
    const streamId = janusStreamMap.value[deviceLocation];
    if (!streamId) {
      console.error(`No stream ID found for location ${deviceLocation}`);
      return;
    }

    janus.value.attach({
      plugin: 'janus.plugin.streaming',
      success: (handle) => {
        pluginHandles.value[macAddress] = handle;
        console.log('Plugin attached:', handle);
        handle.send({ message: { request: 'watch', id: streamId } });
      },
      error: (error) => {
        console.error('Error attaching plugin:', error);
      },
      onmessage: (_msg, jsep) => {
        if (jsep) {
          const pluginHandle = pluginHandles.value[macAddress];
          pluginHandle.createAnswer({
            jsep: jsep,
            media: {
              audioRecv: false,
              videoRecv: true,
              audioSend: false,
              videoSend: false,
            },
            success: (ourJsep) => {
              pluginHandle.send({ message: { request: 'start' }, jsep: ourJsep });
            },
            error: (error) => {
              console.error('WebRTC error:', error);
            },
          });
        }
      },
      onremotetrack: (track, _mid, added) => {
        if (track.kind === 'video' && added) {
          const videoElement = document.getElementById(`video-${macAddress}`);
          if (videoElement) {
            const mediaStream = new MediaStream();
            mediaStream.addTrack(track.clone());
            videoElement.srcObject = mediaStream;
          } else {
            console.error(`Video element with id video-${macAddress} not found`);
          }
        }
      },
      oncleanup: () => {
        console.log('Plugin cleaned up');
      },
      ondetached: () => {
        console.log('Plugin detached');
      },
    });
  });
};


// Start or stop streaming for all selected streams
const toggleStream = async () => {
  if (isStreaming.value) {
    stopJanus();
    isStreaming.value = false;
    isLedOn.value = false;
  } else {
    isLoading.value = true;
    try {
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate delay
      if (selectedStreams.value.length > 0) {
        startJanus();
        isStreaming.value = true;
        isLedOn.value = true;
      } else {
        console.error('No streams selected');
      }
    } catch (error) {
      console.error('Failed to start the streams:', error);
    } finally {
      isLoading.value = false;
    }
  }
};

// Stop Janus and detach plugins
const stopJanus = () => {
  Object.values(pluginHandles.value).forEach(handle => {
    if (handle) {
      handle.hangup();
      handle.detach();
    }
  });
  pluginHandles.value = [];

  if (janus.value) {
    janus.value.destroy();
    janus.value = null;
  }
};

onMounted(fetchStreams);
setInterval(fetchStreams, 10000);
</script>

<style scoped>
.selected-chip {
  background-color: #0057da !important; /* Ensure the selected chip color persists */
}
.fade-enter-active, .fade-leave-active {
  transition: all 0.3s ease;
}
.fade-enter, .fade-leave-to /* .fade-leave-active in <2.1.8 */ {
  opacity: 0;
}
</style>
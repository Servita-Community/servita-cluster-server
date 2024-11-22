<template>
  <v-container fluid>

    <!-- API Alerts -->
    <v-row justify="center">
      <v-col cols="12" md="8" lg="6">
        <v-alert
          v-if="apiSuccessMessage"
          type="success"
          dismissible
          @input="apiSuccessMessage = ''"
          class="mb-4"
        >
          {{ apiSuccessMessage }}
        </v-alert>
        <v-alert
          v-if="apiErrorMessage"
          type="error"
          dismissible
          @input="apiErrorMessage = ''"
          class="mb-4"
        >
          {{ apiErrorMessage }}
        </v-alert>
      </v-col>
    </v-row>

    <v-expansion-panels>
      <v-expansion-panel
        title="Playback Controls"
        :style="{ maxWidth: '600px' }"
        class="mx-auto"
      >
        <v-expansion-panel-text>
          <v-card flat class="justify-center">
            <v-divider />
            <v-card-text>
              <!-- Device Selection -->
              <v-row class="align-center">
                <v-col cols="3" class="text-right">
                  <label for="device">Device:</label>
                </v-col>
                <v-col cols="9">
                  <v-select
                    id="device"
                    v-model="device"
                    append-icon="mdi-camera"
                    :items="deviceList"
                    item-title="location"
                    hide-details
                  />
                </v-col>
              </v-row>
              <!-- Start Time Picker -->
              <v-row class="align-center">
                <v-col cols="3" class="text-right">
                  <label for="start_time">Start Time:</label>
                </v-col>
                <v-col cols="9">
                  <v-dialog
                    v-model="dateTimeDialog"
                    max-width="800px"
                    class="justify-center"
                  >
                    <template v-slot:activator="{ props: activatorProps }">
                      <v-text-field
                        v-model="formattedDateTime"
                        label="Select Date and Time"
                        append-icon="mdi-calendar-clock"
                        readonly
                        v-bind="activatorProps"
                        hide-details
                      ></v-text-field>
                    </template>
                    <v-card class="justify-center">
                      <v-alert
                        v-if="alertMessage"
                        type="error"
                        dismissible
                        @input="alertMessage = ''"
                      >
                        {{ alertMessage }}
                      </v-alert>
                      <v-row>
                        <v-col class="justify-center">
                          <v-date-picker
                            v-model="date"
                            :max="maxDate"
                            :min="minDate"
                            no-title
                            scrollable
                          ></v-date-picker>
                        </v-col>
                        <v-col class="justify-center">
                          <v-time-picker
                            v-model="time"
                            full-width
                            format="24hr"
                          ></v-time-picker>
                        </v-col>
                      </v-row>
                      <v-row class="justify-center">
                        <v-col class="d-flex justify-center">
                          <v-btn
                            class="mb-4"
                            color="primary"
                            @click="saveDateTime"
                          >
                            Save
                          </v-btn>
                        </v-col>
                      </v-row>
                    </v-card>
                  </v-dialog>
                </v-col>
              </v-row>

              <!-- Live Checkbox -->
              <v-row class="align-center">
                <v-col cols="3" class="text-right">
                  <label for="live">Live:</label>
                </v-col>
                <v-col cols="9" class="py-0">
                  <v-checkbox id="live" v-model="live" hide-details />
                </v-col>
              </v-row>

              <!-- Duration -->
              <v-row class="align-center">
                <v-col cols="3" class="text-right">
                  <label for="duration" :style="{ color: live ? 'grey' : 'inherit' }">Duration:</label>
                </v-col>
                <v-col cols="9">
                  <v-text-field
                    id="duration"
                    v-model="duration"
                    type="number"
                    :disabled="live"
                    append-icon="mdi-timer"
                    hint="Duration in minutes"
                    persistent-hint
                  />
                </v-col>
              </v-row>

              <!-- Request Video -->
              <v-row class="justify-center">
                <v-col cols="12" class="d-flex justify-center">
                  <v-btn
                    color="primary"
                    @click="requestVideo"
                    :disabled="!device || (!live && (!duration || duration <= 0))"
                  >
                    Request Video
                  </v-btn>
                </v-col>
              </v-row>

            </v-card-text>
          </v-card>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <v-divider class="my-4" />

    <!-- TODO: Video Player -->

  </v-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import axios from 'axios';
import { format, subHours, addDays } from 'date-fns';
import { VTimePicker } from 'vuetify/lib/labs/components.mjs';

const deviceList = ref([]);
const device = ref('');
const start_time = ref(new Date());
const duration = ref(0);
const live = ref(false);
const dateTimeDialog = ref(false);
const alertMessage = ref('');
const currentTime = ref(Date.now());
const apiErrorMessage = ref('');
const apiSuccessMessage = ref('');

const maxDate = format(addDays(new Date(), 0), 'yyyy-MM-dd');
const minDate = format(subHours(new Date(), 48), 'yyyy-MM-dd');

// Separate refs for date and time pickers
const date = ref(new Date());
const time = ref(format(new Date(), 'HH:mm'));

// Computed property for formatted date and time
const formattedDateTime = computed(() =>
  format(start_time.value, 'yyyy-MM-dd HH:mm')
);

// Method to handle date and time selection
const saveDateTime = () => {
  const [hours, minutes] = time.value.split(':').map(Number);
  const selectedDate = new Date(date.value);
  selectedDate.setHours(hours);
  selectedDate.setMinutes(minutes);
  selectedDate.setSeconds(0);
  selectedDate.setMilliseconds(0);

  const now = new Date();
  const time48HoursAgo = subHours(now, 48);

  if (selectedDate > now) {
    alertMessage.value = 'Selected time cannot be in the future.';
  } else if (selectedDate < time48HoursAgo) {
    alertMessage.value = 'Selected time cannot be more than 48 hours ago.';
  } else {
    start_time.value = selectedDate;
    dateTimeDialog.value = false; // Close the dialog
    alertMessage.value = ''; // Clear any previous alert
  }
};

// Fetch devices from the API
const getDevices = async () => {
  try {
    const response = await axios.get(`http://0.0.0.0:8000/api/devices/statuses/`);
    const devices = response.data;

    const locationCount = devices.reduce((acc, device) => {
      const location = device.location || device.mac_address;
      acc[location] = (acc[location] || 0) + 1;
      return acc;
    }, {});

    deviceList.value = devices.map((device) => {
      let location = device.location || device.mac_address;
      if (locationCount[location] > 1) {
        location = `${location} - ${device.mac_address}`;
      }
      return { ...device, location };
    });

    console.log(deviceList.value);
  } catch (error) {
    console.error(error);
  }
};

const requestVideo = async () => {
  try {
    const response = await axios.post(
      `http://${window.location.hostname}:${window.location.port}/api/recordings/`,
      {
        device: device.value.mac_address,
        start_time: start_time.value,
        duration: live ? 0 : duration.value,
      }
    );
    // Set success message and clear error message
    apiSuccessMessage.value = 'Video request was successful!';
    apiErrorMessage.value = '';
    console.log(response.data);
  } catch (error) {
    // Clear success message and set error message
    apiSuccessMessage.value = '';
    if (error.response && error.response.data && error.response.data.detail) {
      apiErrorMessage.value = error.response.data.detail;
    } else {
      apiErrorMessage.value = 'An error occurred while requesting the video.';
    }
    console.error(error);
  }
};

// Watchers to clear alerts after 5 seconds
watch(apiSuccessMessage, (newValue) => {
  if (newValue) {
    setTimeout(() => {
      apiSuccessMessage.value = '';
    }, 5000);
  }
});

watch(apiErrorMessage, (newValue) => {
  if (newValue) {
    setTimeout(() => {
      apiErrorMessage.value = '';
    }, 5000);
  }
});

onMounted(() => {
  setInterval(() => {
    // Ping the server
  }, 30000);

  setInterval(() => {
    currentTime.value = Date.now();
  }, 1000);

  getDevices();

  // Initialize date and time pickers with the current start_time
  date.value = start_time.value;
  time.value = format(start_time.value, 'HH:mm');
});

onUnmounted(() => {
  // Stop the video
});
</script>

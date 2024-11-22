<template>
  <v-container fluid>
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
                <v-col cols="2" class="text-right">
                  <label for="device">Device:</label>
                </v-col>
                <v-col cols="8">
                  <v-select
                    id="device"
                    v-model="device"
                    :items="deviceList"
                    item-title="location"
                    hide-details
                  />
                </v-col>
              </v-row>
              <!-- Start Time Picker -->
              <v-row class="align-center">
                <v-col cols="2" class="text-right">
                  <label for="start_time">Start Time:</label>
                </v-col>
                <v-col cols="8">
                  <v-dialog v-model="dateTimeDialog" max-width="500">
                    <template v-slot:activator="{ props: activatorProps }">
                      <v-text-field
                        v-model="formattedDateTime"
                        label="Select Date and Time"
                        prepend-icon="mdi-calendar-clock"
                        readonly
                        v-bind="activatorProps"
                        hide-details
                      ></v-text-field>
                    </template>
                    <template v-slot:default="{ getting_time }">
                      <v-card justify="center">
                        <v-row class="justify-center">
                          <v-col>
                            <v-date-picker
                              v-model="date"
                              :max="new Date(maxDate)"
                              :min="new Date(minDate)"
                              no-title
                              scrollable
                            ></v-date-picker>
                          </v-col>
                          <v-col>
                            <v-time-picker
                              v-model="time"
                              full-width
                              format="24hr"
                            ></v-time-picker>
                            <v-btn
                              color="primary"
                              @click="saveDateTime; getting_time = false"
                            >Save</v-btn>
                          </v-col>
                        </v-row>
                      </v-card>
                    </template>
                  </v-dialog>
                </v-col>
              </v-row>
              <!-- Duration -->
              <v-row class="align-center">
                <v-col cols="2" class="text-right">
                  <label for="duration">Duration:</label>
                </v-col>
                <v-col cols="8">
                  <v-text-field
                    id="duration"
                    v-model="duration"
                    type="number"
                    hide-details
                  />
                </v-col>
              </v-row>
              <!-- Live Checkbox -->
              <v-row class="align-center">
                <v-col cols="2" class="text-right">
                  <label for="live">Live:</label>
                </v-col>
                <v-col cols="8">
                  <v-checkbox id="live" v-model="live" hide-details />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </v-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import axios from 'axios';
import { format, subHours } from 'date-fns';
import { VTimePicker } from 'vuetify/labs/VTimePicker'

const deviceList = ref([]);
const device = ref('');
const start_time = ref(new Date());
const duration = ref(0);
const live = ref(false);
const dateTimeDialog = ref(false);
const currentTime = ref(Date.now());

const maxDate = format(new Date(), 'yyyy-MM-dd');
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
  // Combine date and time into a single Date object
  const [hours, minutes] = time.value.split(':').map(Number);
  const selectedDate = new Date(date.value);
  selectedDate.setHours(hours);
  selectedDate.setMinutes(minutes);
  selectedDate.setSeconds(0);
  selectedDate.setMilliseconds(0);
  start_time.value = selectedDate;
  dateTimeDialog.value = false; // Close the dialog
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

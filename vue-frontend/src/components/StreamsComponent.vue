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
          :items="cameras"
          item-title="description"
          item-value="index"
          label="Select Stream"
          outlined
        ></v-select>
      </v-card-actions>
    </v-card>

    <v-divider class="my-8"/>

    <!-- Stream Video -->
    <v-card justify="center" class="mx-auto">
      <v-card-title class="text-center text-h6">
        Stream Video
      </v-card-title>
      <v-card-text class="text-center">
        <v-img
          v-if="isStreaming"
          :src="selectedStream ? `http://${selectedStream.ip}` : null"
          width="100%"
          height="auto"
        ></v-img>
        <v-card-text v-else>
          <v-card-text class="text-center">
            Select a stream to view
          </v-card-text>
        </v-card-text>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { inject, ref } from 'vue'

const isLedOn = ref(false)
const isStreaming = ref(false)
const isLoading = ref(false)

const cameras = inject('cameras')
const selectedStream = ref(null)

const toggleStream = async () => {
  if (isStreaming.value) {
    // Stop the stream
    isStreaming.value = false
    isLedOn.value = false
  } else {
    // Start the stream
    isLoading.value = true
    try {
      // Simulate stream connection delay
      await new Promise(resolve => setTimeout(resolve, 2000))
      if (selectedStream.value) {
        isStreaming.value = true
        isLedOn.value = true
      } else {
        console.error('No stream selected or invalid stream')
      }
    } catch (error) {
      console.error('Failed to start the stream:', error)
    } finally {
      isLoading.value = false
    }
  }
}

</script>

<style scoped>
</style>
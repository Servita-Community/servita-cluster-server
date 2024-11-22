<template>
  <v-container fluid>
    <v-card justify="center">
      <v-card-title class="text-center text-h6">
        Settings Page
      </v-card-title>
      <v-card-text class="text-center">
        <v-icon :color="isLedOn ? 'green' : 'red'">
          {{ isLedOn ? 'mdi-led-on' : 'mdi-led-off' }}
        </v-icon>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const isLedOn = ref(false)

const toggleLed = () => {
  isLedOn.value = !isLedOn.value
}

let intervalId

onMounted(() => {
  intervalId = setInterval(toggleLed, 1000)
})

onUnmounted(() => {
  clearInterval(intervalId)
})
</script>

<style scoped>
</style>
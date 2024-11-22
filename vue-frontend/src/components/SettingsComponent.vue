<template>
  <v-container fluid>
    <v-card justify="center">
      <v-card-title class="text-center text-h6">
        Settings Page
      </v-card-title>
      <v-divider />
      <v-card-text class="text-center">
        <v-text-field v-model="baseport.front" type="number" />
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
const baseport = ref({"front": 5000, "backend": 5000});

// TODO: UDP/TCP slider

// TODO: 
</script>

<style scoped>
</style>
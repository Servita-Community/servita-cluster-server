<template>
  <v-app :scrollable="false">
    <NavbarComponent />
    <v-main :scrollable="false">
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup>
import NavbarComponent from './components/NavbarComponent.vue';
import { ref, provide, onMounted } from 'vue'
import { fetchCameras } from './apiTools'

const cameras = ref([])
provide('cameras', cameras)

onMounted(async () => {
  cameras.value = await fetchCameras()
})

</script>

<style scoped>
#app {
  height: 100%;
}

</style>
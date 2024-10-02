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

</script>

<style scoped>
#app {
  height: 100%;
}

</style>
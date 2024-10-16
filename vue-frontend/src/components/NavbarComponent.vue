<template>
  <v-container fluid>
    <v-app-bar app>
      <v-app-bar-nav-icon @click="leftDrawer = !leftDrawer" class="d-flex align-center"></v-app-bar-nav-icon>
      <v-spacer />
      <v-img 
        src="../../public/ubihere.webp" 
        class="logo" 
        width="auto" 
        @click="$router.replace('/')"
        style="cursor: pointer;"
      ></v-img>
      <v-spacer />
      <v-app-bar-nav-icon @click="rightDrawer = !rightDrawer" class="d-flex align-center">
        <v-icon>mdi-camera</v-icon>
      </v-app-bar-nav-icon>
    </v-app-bar>
    <v-navigation-drawer app v-model="leftDrawer">
      <v-list>
        <router-link
          v-for="route in routes.filter(route => route.path !== '/')"
          :key="route.path"
          :to="route.path"
          style="text-decoration: none; color: inherit;"
        >
          <v-list-item link>
            <template v-slot:prepend>
              <v-icon>{{ route.icon }}</v-icon>
            </template>
            <v-list-item-title v-text="route.name"></v-list-item-title>
          </v-list-item>
        </router-link>
      </v-list>
    </v-navigation-drawer>

    <v-navigation-drawer app v-model="rightDrawer" temporary location="right">
      <v-expansion-panels>
        <v-expansion-panel
          v-for="camera in cameras"
          :key="camera.index"
        >
          <v-expansion-panel-title>
            <span class="text-h4 mr-4">{{ camera.index }}</span>
            <span>{{ camera.description }}</span>
            <v-spacer></v-spacer>
            <v-icon :color="camera.active ? 'green' : 'red'">mdi-circle</v-icon>
          </v-expansion-panel-title>

          <v-expansion-panel-text>
            <v-list>
              <v-list-item
                :href="'http://' + camera.ip"
                prepend-icon="mdi-camera-wireless"
              >
                <v-list-item-title>View Camera Stream</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-navigation-drawer>
  </v-container>
</template>

<script setup>
import { ref, inject } from 'vue'
import routes from '../routes'

const cameras = inject('cameras')

const leftDrawer = ref(false)
const rightDrawer = ref(false)

</script>

<style scoped>
.logo {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}
</style>

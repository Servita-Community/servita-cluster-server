import { createApp } from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify'
import { createRouter, createWebHistory } from 'vue-router'
import routes from './routes'
import { loadFonts } from './plugins/webfontloader'

loadFonts()

const router = createRouter({
  history: createWebHistory(),
  routes,
})

createApp(App)
  .use(vuetify)
  .use(router)
  .mount('#app')

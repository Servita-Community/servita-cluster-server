// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Vuetify
import { createVuetify } from 'vuetify'

export default createVuetify({
  theme: {
    defaultTheme: 'dark',
  },
  icons: {
    iconfont: 'mdi',
  },
  // https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
})
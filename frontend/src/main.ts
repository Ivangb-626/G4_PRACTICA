import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { setupRouteGuards } from './router/guards'
import './styles/theme.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
setupRouteGuards(router)
app.mount('#app')

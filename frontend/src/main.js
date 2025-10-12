import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import router from './router/router.js'
import { initPerformanceTracking } from './services/performanceTracker'

// Initialize real Chrome performance tracking
initPerformanceTracking()

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.mount('#app')

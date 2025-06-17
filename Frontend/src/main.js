import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // Importa il router

const app = createApp(App)
app.use(router) // Usa il router
app.mount('#app')
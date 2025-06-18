import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // Importa il router
import store from './store'; // <-- AGGIUNGI QUESTO
import '@fortawesome/fontawesome-free/css/all.css'

const app = createApp(App)
app.use(store); // <-- AGGIUNGI QUESTO
app.use(router) // Usa il router
app.mount('#app')
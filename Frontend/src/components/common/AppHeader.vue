<template>
  <header class="app-header">
    <div class="container">
      <div class="logo">PeerReview<span class="highlight">App</span></div>
    </div>
    <!-- Aggiungi i pulsanti di navigazione solo se l'utente è loggato e non è nella dashboard o auth pages -->
    <NavigationButtons v-if="isLoggedIn && !isDashboardPage && !isAuthPage" />
  </header>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import NavigationButtons from './NavigationButtons.vue';

const route = useRoute();

const isLoggedIn = computed(() => !!localStorage.getItem('userToken'));

// Controlla se siamo in una pagina dashboard
const isDashboardPage = computed(() => {
  return route.path.includes('/dashboard');
});

// Controlla se siamo in pagine di autenticazione (login/register)
const isAuthPage = computed(() => {
  return route.path === '/login' || route.path === '/register';
});
</script>

<style scoped>
.app-header {
  background: #ffffff;
  color: #333;
  padding: 1rem 0;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  position: fixed;
  width: 100%;
  top: 0;
  left: 0;
  z-index: 1000;
}

.container {
  max-width: 1100px;
  margin: auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  font-size: 1.8rem;
  font-weight: bold;
  color: #2c3e50;
}

.logo .highlight {
  color: #42b983;
}

nav a {
  color: #333;
  margin-left: 15px;
  text-decoration: none;
  font-weight: 500;
}
nav a:hover, nav a.router-link-exact-active {
  color: #42b983;
}
</style>
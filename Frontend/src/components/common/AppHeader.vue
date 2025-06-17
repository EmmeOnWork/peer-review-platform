<template>
  <header class="app-header">
    <div class="container">
      <div class="logo">PeerReview<span class="highlight">App</span></div>
      <nav v-if="isLoggedIn">
        <!-- Esempio di link basati sul ruolo -->
        <router-link v-if="userRole === 'teacher'" to="/teacher/dashboard">Dashboard Docente</router-link>
        <!-- <router-link v-if="userRole === 'teacher'" to="/teacher/assignments">Miei Assignment</router-link> -->
        <router-link v-if="userRole === 'student'" to="/student/dashboard">Dashboard Studente</router-link>
        <!-- <router-link v-if="userRole === 'student'" to="/student/assignments">Miei Assignment</router-link> -->
        <button @click="performLogout" class="logout-btn">Logout</button>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const isLoggedIn = computed(() => !!localStorage.getItem('userToken'));
const userRole = computed(() => localStorage.getItem('userRole'));

function performLogout() {
  localStorage.removeItem('userToken');
  localStorage.removeItem('userRole');
  router.push('/login');
}
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
.logout-btn {
  background: #e74c3c;
  color: #fff;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.9rem;
  margin-left: 15px;
  transition: background-color 0.3s ease;
}
.logout-btn:hover {
  background: #c0392b;
}
</style>
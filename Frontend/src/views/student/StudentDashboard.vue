<template>
  <div class="dashboard student-dashboard">
    <AppHeader />
    <UserProfile />
    <main>
      <h1>Dashboard Studente</h1>
      <p>Benvenuto, Studente!</p>
      <p>Qui troverai i tuoi assignment e potrai effettuare le peer review.</p>
      <!-- TODO: Link a /student/assignments, ecc. -->
      <button @click="logout">Logout</button>
    </main>
  </div>
</template>

<script setup>
import AppHeader from '@/components/common/AppHeader.vue';
import UserProfile from '@/components/auth/UserProfile.vue';
import { useRouter } from 'vue-router';
const router = useRouter();
function logout() {
  localStorage.removeItem('userToken');
  localStorage.removeItem('userRole');
  router.push('/login');
}
</script>

<style scoped>
.student-dashboard { /* Stili specifici se necessario */ }
main { padding: 20px; margin-top: 60px; }
</style>
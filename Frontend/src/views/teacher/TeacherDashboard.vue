<template>
  <div class="dashboard teacher-dashboard">
    <AppHeader />
    <UserProfile />
    <main>
      <h1>Dashboard Docente</h1>
      <p>Benvenuto, Docente!</p>
      <p>Qui potrai creare e gestire i tuoi assignment.</p>
      <!-- TODO: Link a /teacher/assignments, ecc. -->
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
.teacher-dashboard { /* Stili specifici se necessario */ }
main { padding: 20px; margin-top: 60px; /* Spazio per AppHeader fisso */ }
</style>
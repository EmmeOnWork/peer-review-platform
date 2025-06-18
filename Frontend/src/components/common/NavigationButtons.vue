<template>
  <div class="navigation-buttons">
    <button @click="goBack" class="nav-btn back-btn" title="Torna indietro">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M15 18L9 12L15 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>
    <button @click="goHome" class="nav-btn home-btn" title="Vai alla dashboard">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 9L12 2L21 9V20C21 20.5304 20.7893 21.0391 20.4142 21.4142C20.0391 21.7893 19.5304 22 19 22H5C4.46957 22 3.96086 21.7893 3.58579 21.4142C3.21071 21.0391 3 20.5304 3 20V9Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M9 22V12H15V22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { computed } from 'vue';

const router = useRouter();

const userRole = computed(() => localStorage.getItem('userRole'));

const goBack = () => {
  router.go(-1);
};

const goHome = () => {
  if (userRole.value === 'teacher') {
    router.push('/teacher/dashboard');
  } else if (userRole.value === 'student') {
    router.push('/student/dashboard');
  } else {
    router.push('/login');
  }
};
</script>

<style scoped>
.navigation-buttons {
  position: fixed;
  top: 100px; /* Sotto l'header */
  left: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 999;
}

.nav-btn {
  width: 45px;
  height: 45px;
  border: none;
  border-radius: 50%;
  background: #ffffff;
  color: #333;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.nav-btn:hover {
  background: #f8f9fa;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.back-btn:hover {
  color: #007bff;
}

.home-btn:hover {
  color: #28a745;
}

.nav-btn:active {
  transform: translateY(0);
}
</style>
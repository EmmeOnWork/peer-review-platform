<template>
  <div id="app-container">
    <AppHeader />
    <main class="main-content">
      <router-view /> <!-- Qui verranno caricate LoginPage, TeacherDashboard, StudentDashboard, ecc. -->
    </main>
  </div>
</template>

<script setup>
import AppHeader from './components/common/AppHeader.vue';
</script>

<style>
/* Stili globali per l'app, se necessari */
body {
  margin: 0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f0f2f5; /* Sfondo base per l'app */
  color: #333;
}

#app-container {
  min-height: 100vh;
}

.main-content {
  padding-top: 80px; /* Spazio per l'header fisso */
  padding-left: 80px; /* Spazio per i pulsanti di navigazione */
  min-height: calc(100vh - 80px);
}

/* Responsive: su schermi piccoli riduci il padding */
@media (max-width: 768px) {
  .main-content {
    padding-left: 20px;
  }
  
  .navigation-buttons {
    left: 10px;
    top: 90px;
  }
  
  .nav-btn {
    width: 40px;
    height: 40px;
  }
}

/* Puoi aggiungere altri stili globali o utility classes qui */
</style>
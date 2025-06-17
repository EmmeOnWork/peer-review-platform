<template>
  <div id="app-container">
    <router-view /> <!-- Qui verranno caricate LoginPage, TeacherDashboard, StudentDashboard, ecc. -->
  </div>
</template>

<script setup>
// Nessuna logica specifica qui per ora, gestita dal router e dalle view
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

/* Puoi aggiungere altri stili globali o utility classes qui */
</style>
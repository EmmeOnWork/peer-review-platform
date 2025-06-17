<template>
  <div class="registration-page">
    <RegistrationForm />
  </div>
</template>

<script setup>
import RegistrationForm from '@/components/auth/RegistrationForm.vue';
</script>

<style scoped>
.registration-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f4f7f6;
}
</style>
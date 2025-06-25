<template>
  <div class="student-assignments-page">
    <div class="header">
      <div class="header-content">
        <h1><i class="fas fa-tasks"></i> My Assignments</h1>
        <p>Visualizza e gestisci i tuoi assignment</p>
      </div>
    </div>
    <AssignmentListStudent />
  </div>
</template>

<script setup>
import AssignmentListStudent from '@/components/assignment/AssignmentListStudent.vue';
</script>

<style scoped>
.student-assignments-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  background: #f8f9fa;
  min-height: 100vh;
}

.header {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  margin-bottom: 25px;
  text-align: center;
}

.header-content h1 {
  color: #2d3436;
  font-size: 2rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.header-content h1 i {
  color: #6c5ce7;
}

.header-content p {
  color: #636e72;
  font-size: 1.1rem;
  margin: 0;
}

@media (max-width: 768px) {
  .student-assignments-page {
    padding: 10px;
  }
  
  .header {
    padding: 20px;
  }
  
  .header-content h1 {
    font-size: 1.5rem;
  }
}
</style>
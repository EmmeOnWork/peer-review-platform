<template>
  <div class="teacher-assignments-page">
    <h1>My Assignments</h1>
    
    <!-- Button to create new assignment -->
    <button 
      v-if="!showCreateForm && !currentAssignment" 
      @click="showCreateForm = true; currentAssignment = null;" 
      class="create-assignment-btn"
    >
      Create New Assignment
    </button>

    <!-- Form to create/edit assignment -->
    <AssignmentForm 
      v-if="showCreateForm || currentAssignment" 
      :assignment="currentAssignment" 
      @submitted="handleFormSubmitted"
      @cancel="closeForm"
    />

    <!-- Assignment list -->
    <AssignmentListTeacher 
      v-if="!showCreateForm && !currentAssignment" 
      @edit-assignment="editAssignment"
      ref="assignmentListTeacher"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import AssignmentListTeacher from '@/components/assignment/AssignmentListTeacher.vue';
import AssignmentForm from '@/components/assignment/AssignmentForm.vue';

const showCreateForm = ref(false);
const currentAssignment = ref(null);
const assignmentListTeacher = ref(null);

const editAssignment = (assignment) => {
  currentAssignment.value = assignment;
  showCreateForm.value = false;
};

const handleFormSubmitted = () => {
  closeForm();
  // Refresh della lista dopo creazione/modifica
  if (assignmentListTeacher.value) {
    assignmentListTeacher.value.fetchAssignments();
  }
};

const closeForm = () => {
  showCreateForm.value = false;
  currentAssignment.value = null;
};
</script>

<style scoped>
.teacher-assignments-page {
  max-width: 1000px;
  margin: 20px auto;
  padding: 20px;
}

h1 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}

.create-assignment-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  margin-bottom: 20px;
  display: block;
  margin-left: auto;
  margin-right: auto;
}

.create-assignment-btn:hover {
  background-color: #45a049;
}
</style>
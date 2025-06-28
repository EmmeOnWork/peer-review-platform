<template>
  <div class="assignment-list-teacher">
    <div class="header-section">
      <h3><i class="fas fa-tasks"></i> My Assignments</h3>
      <p class="subtitle">Manage and monitor your assignments</p>
    </div>
    
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading assignments...</p>
    </div>
    
    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-triangle"></i>
      {{ error }}
    </div>
    
    <div v-if="!loading && !error && assignments.length === 0" class="no-assignments">
      <i class="fas fa-clipboard-list"></i>
      <h4>No Assignments Created</h4>
      <p>You have not created any assignments yet. Start by creating your first assignment!</p>
    </div>
    
    <div v-if="!loading && !error && assignments.length > 0" class="assignments-grid">
      <div v-for="assignment in paginatedAssignments" :key="assignment._id" class="assignment-card">
        <div class="card-header">
          <h4>{{ assignment.title }}</h4>
          <div class="deadline-badge" :class="getDeadlineClass(assignment.deadline)">
            <i class="fas fa-calendar-alt"></i>
            {{ formatDeadline(assignment.deadline) }}
          </div>
        </div>
        
        <div class="card-body">
          <p class="description">{{ assignment.description }}</p>
          <div class="assignment-meta">
            <span class="meta-item">
              <i class="fas fa-clock"></i>
              Deadline: {{ new Date(assignment.deadline).toLocaleDateString() }}
            </span>
          </div>
        </div>
        
        <div class="card-actions">
          <button @click="viewDetails(assignment._id)" class="action-btn primary-btn">
            <i class="fas fa-eye"></i>
            View Details
          </button>
          <button @click="editAssignment(assignment)" class="action-btn secondary-btn">
            <i class="fas fa-edit"></i>
            Edit
          </button>
          <button @click="confirmDelete(assignment._id)" class="action-btn danger-btn">
            <i class="fas fa-trash"></i>
            Delete
          </button>
        </div>
      </div>
    </div>
    
    <!-- Paginazione -->
    <div v-if="assignments.length > itemsPerPage" class="pagination">
      <button 
        v-if="hasMoreItems" 
        @click="showMore" 
        class="load-more-btn"
      >
        <i class="fas fa-plus"></i>
        Show more ({{ remainingItems }} remaining)
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const assignments = ref([]);
const loading = ref(true);
const error = ref(null);
const currentPage = ref(1);
const itemsPerPage = ref(10);

// Emit per comunicare con il componente padre
const emit = defineEmits(['edit-assignment']);

// Computed per la paginazione
const paginatedAssignments = computed(() => {
  const endIndex = currentPage.value * itemsPerPage.value;
  return assignments.value.slice(0, endIndex);
});

const hasMoreItems = computed(() => {
  return assignments.value.length > currentPage.value * itemsPerPage.value;
});

const remainingItems = computed(() => {
  return assignments.value.length - (currentPage.value * itemsPerPage.value);
});

const showMore = () => {
  currentPage.value++;
};

const API_URL = '/assignments';

const getAuthHeaders = () => {
  const token = localStorage.getItem('userToken');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

async function fetchAssignments() {
  loading.value = true;
  error.value = null;
  try {
    const response = await axios.get(`${API_URL}/teacher/mine`, { headers: getAuthHeaders() });
    assignments.value = response.data;
  } catch (err) {
    console.error('Error fetching teacher assignments:', err.response || err.message);
    error.value = err.response?.data?.message || 'Failed to load assignments. Please try again.';
  } finally {
    loading.value = false;
  }
}

// Modifica la funzione viewDetails
function viewDetails(assignmentId) {
  router.push(`/teacher/assignments/${assignmentId}/submissions`);
}

function editAssignment(assignment) {
  // Emette l'evento al componente padre per gestire l'editing
  emit('edit-assignment', assignment);
}

async function confirmDelete(assignmentId) {
  if (confirm('Are you sure you want to delete this assignment?')) {
    try {
      await axios.delete(`${API_URL}/${assignmentId}`, { headers: getAuthHeaders() });
      assignments.value = assignments.value.filter(a => a._id !== assignmentId);
      alert('Assignment deleted successfully.');
    } catch (err) {
      console.error('Error deleting assignment:', err.response || err.message);
      alert(err.response?.data?.message || 'Failed to delete assignment.');
    }
  }
}

// Espone la funzione per il refresh dal componente padre
defineExpose({
  fetchAssignments
});

onMounted(() => {
  fetchAssignments();
});

// Aggiungi queste nuove funzioni
const getDeadlineClass = (deadline) => {
  const now = new Date();
  const deadlineDate = new Date(deadline);
  const diffDays = Math.ceil((deadlineDate - now) / (1000 * 60 * 60 * 24));
  
  if (diffDays < 0) return 'expired';
  if (diffDays <= 3) return 'urgent';
  if (diffDays <= 7) return 'warning';
  return 'normal';
};

const formatDeadline = (deadline) => {
  const now = new Date();
  const deadlineDate = new Date(deadline);
  const diffDays = Math.ceil((deadlineDate - now) / (1000 * 60 * 60 * 24));
  
  if (diffDays < 0) return 'Expired';
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Tomorrow';
  return `${diffDays} days`;
};
</script>

<style scoped>
.assignment-list-teacher {
  padding: 24px;
  background-color: #f8f9fa;
  min-height: 100vh;
}

.header-section {
  text-align: center;
  margin-bottom: 32px;
  padding: 24px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.header-section h3 {
  font-size: 2.5rem;
  margin: 0 0 8px 0;
  font-weight: 700;
  color: #2c3e50;
}

.header-section i {
  color: #3498db;
  margin-right: 12px;
}

.subtitle {
  font-size: 1.1rem;
  color: #6c757d;
  margin: 0;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  color: #6c757d;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e9ecef;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  background: #fff5f5;
  border: 1px solid #fed7d7;
  color: #e53e3e;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.no-assignments {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  color: #6c757d;
}

.no-assignments i {
  font-size: 4rem;
  margin-bottom: 16px;
  color: #dee2e6;
}

.no-assignments h4 {
  font-size: 1.5rem;
  margin: 0 0 8px 0;
  color: #495057;
}

.assignments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.assignment-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  transition: all 0.3s ease;
  border: 1px solid #e9ecef;
}

.assignment-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.card-header {
  padding: 20px 20px 16px 20px;
  border-bottom: 1px solid #f8f9fa;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.card-header h4 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
  flex: 1;
}

.deadline-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 12px;
}

.deadline-badge.normal {
  background: #d4edda;
  color: #155724;
}

.deadline-badge.warning {
  background: #fff3cd;
  color: #856404;
}

.deadline-badge.urgent {
  background: #f8d7da;
  color: #721c24;
}

.deadline-badge.expired {
  background: #f8f9fa;
  color: #6c757d;
}

.card-body {
  padding: 16px 20px;
}

.description {
  color: #6c757d;
  line-height: 1.5;
  margin: 0 0 16px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.assignment-meta {
  display: flex;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
  color: #6c757d;
}

.meta-item i {
  color: #3498db;
}

.card-actions {
  padding: 16px 20px 20px 20px;
  display: flex;
  gap: 8px;
}

.action-btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.primary-btn {
  background: #3498db;
  color: white;
}

.primary-btn:hover {
  background: #2980b9;
  transform: translateY(-1px);
}

.secondary-btn {
  background: #f39c12;
  color: white;
}

.secondary-btn:hover {
  background: #e67e22;
  transform: translateY(-1px);
}

.danger-btn {
  background: #e74c3c;
  color: white;
}

.danger-btn:hover {
  background: #c0392b;
  transform: translateY(-1px);
}

.pagination {
  text-align: center;
  margin-top: 32px;
}

.load-more-btn {
  background: white;
  color: #3498db;
  border: 2px solid #3498db;
  padding: 12px 24px;
  border-radius: 25px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.load-more-btn:hover {
  background: #3498db;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
}
</style>
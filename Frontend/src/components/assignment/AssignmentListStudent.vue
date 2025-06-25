<template>
  <div class="assignment-list">
    <!-- Loading -->
    <div v-if="loading" class="loading">
      <i class="fas fa-spinner fa-spin"></i>
      <span>Caricamento assignment...</span>
    </div>

    <!-- Error -->
    <div v-if="error" class="error">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && !error && assignments.length === 0" class="empty">
      <i class="fas fa-clipboard-list"></i>
      <h3>Nessun Assignment</h3>
      <p>Non ci sono assignment disponibili al momento.</p>
    </div>

    <!-- Assignments Grid -->
    <div v-if="!loading && !error && assignments.length > 0" class="assignments-grid">
      <div v-for="assignment in paginatedAssignments" :key="assignment._id" class="assignment-card">
        <!-- Header -->
        <div class="card-header">
          <h3>{{ assignment.title }}</h3>
          <span class="deadline" :class="{ 'urgent': isUrgent(assignment.deadline) }">
            <i class="fas fa-clock"></i>
            {{ formatDate(assignment.deadline) }}
          </span>
        </div>

        <!-- Content -->
        <div class="card-content">
          <div class="description">
            <i class="fas fa-align-left"></i>
            <span>{{ assignment.description }}</span>
          </div>
          
          <div class="teacher">
            <i class="fas fa-user-tie"></i>
            <span>{{ assignment.teacherName }} {{ assignment.teacherSurname }}</span>
          </div>

          <!-- Rubric Preview -->
          <div v-if="assignment.rubric?.length" class="rubric-preview">
            <i class="fas fa-list-check"></i>
            <span>{{ assignment.rubric.length }} criteri di valutazione</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="card-actions">
          <button @click="submitAssignment(assignment._id)" class="submit-btn">
            <i class="fas fa-paper-plane"></i>
            Submit Assignment
          </button>
        </div>
      </div>
    </div>

    <!-- Load More -->
    <div v-if="hasMoreItems" class="load-more">
      <button @click="showMore" class="load-more-btn">
        <i class="fas fa-chevron-down"></i>
        Mostra altri ({{ remainingItems }})
      </button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

export default {
  name: 'AssignmentListStudent',
  setup() {
    const router = useRouter();
    const assignments = ref([]);
    const loading = ref(true);
    const error = ref(null);
    const currentPage = ref(1);
    const itemsPerPage = ref(6);

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

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A';
      return new Date(dateString).toLocaleDateString('it-IT', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    };

    const isUrgent = (deadline) => {
      if (!deadline) return false;
      const now = new Date();
      const deadlineDate = new Date(deadline);
      const diffDays = (deadlineDate - now) / (1000 * 60 * 60 * 24);
      return diffDays <= 3;
    };

    const getAuthHeaders = () => {
      const token = localStorage.getItem('userToken');
      return token ? { Authorization: `Bearer ${token}` } : {};
    };

    const submitAssignment = (assignmentId) => {
      router.push(`/student/assignments/${assignmentId}/submit`);
    };

    const fetchAssignments = async () => {
      try {
        const response = await axios.get('/assignments/student/mine', {
          headers: getAuthHeaders()
        });
        assignments.value = response.data;
      } catch (err) {
        console.error('Error fetching assignments:', err);
        error.value = 'Errore nel caricamento degli assignment.';
      } finally {
        loading.value = false;
      }
    };

    onMounted(fetchAssignments);

    return {
      assignments, loading, error, paginatedAssignments,
      hasMoreItems, remainingItems, showMore, formatDate,
      isUrgent, submitAssignment
    };
  }
};
</script>

<style scoped>
.assignment-list {
  padding: 0;
}

.loading, .error, .empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  text-align: center;
}

.loading {
  gap: 15px;
}

.loading i {
  font-size: 2rem;
  color: #6c5ce7;
}

.error {
  gap: 10px;
}

.error i {
  font-size: 3rem;
  color: #e74c3c;
}

.empty i {
  font-size: 4rem;
  color: #ddd;
  margin-bottom: 20px;
}

.empty h3 {
  color: #2d3436;
  margin: 0 0 10px 0;
}

.empty p {
  color: #636e72;
  margin: 0;
}

.assignments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.assignment-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.assignment-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}

.card-header {
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 15px;
}

.card-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  flex: 1;
}

.deadline {
  background: rgba(255,255,255,0.2);
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.deadline.urgent {
  background: #e74c3c;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.card-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.description, .teacher, .rubric-preview {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 0.95rem;
}

.description i, .teacher i, .rubric-preview i {
  color: #6c5ce7;
  margin-top: 2px;
  flex-shrink: 0;
}

.description span {
  color: #2d3436;
  line-height: 1.4;
}

.teacher span {
  color: #636e72;
  font-weight: 500;
}

.rubric-preview span {
  color: #00b894;
  font-weight: 500;
}

.card-actions {
  padding: 20px;
  border-top: 1px solid #f1f3f4;
}

.submit-btn {
  width: 100%;
  background: linear-gradient(135deg, #00b894, #00cec9);
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.submit-btn:hover {
  background: linear-gradient(135deg, #00a085, #00b7b3);
  transform: translateY(-1px);
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

.load-more-btn {
  background: white;
  color: #6c5ce7;
  border: 2px solid #6c5ce7;
  padding: 12px 30px;
  border-radius: 25px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.load-more-btn:hover {
  background: #6c5ce7;
  color: white;
}

@media (max-width: 768px) {
  .assignments-grid {
    grid-template-columns: 1fr;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
  }
  
  .deadline {
    align-self: flex-start;
  }
}
</style>
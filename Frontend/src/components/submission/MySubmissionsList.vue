<template>
  <div class="my-submissions-list">
    <!-- Loading -->
    <div v-if="loading" class="loading">
      <i class="fas fa-spinner fa-spin"></i>
      <span>Caricamento submission...</span>
    </div>

    <!-- Error -->
    <div v-if="error" class="error">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>
    
    <!-- Empty State -->
    <div v-if="!loading && !error && submissions.length === 0" class="empty">
      <i class="fas fa-inbox"></i>
      <h3>Nessuna Submission</h3>
      <p>Non hai ancora inviato nessuna submission.</p>
    </div>
    
    <!-- Submissions Table -->
    <div v-if="!loading && !error && submissions.length > 0" class="submissions-container">
      <div class="table-card">
        <div class="table-header">
          <h3><i class="fas fa-list"></i> Le Tue Submission</h3>
          <span class="count">{{ submissions.length }} submission</span>
        </div>
        
        <div class="table-content">
          <div class="table-responsive">
            <table class="submissions-table">
              <thead>
                <tr>
                  <th><i class="fas fa-tasks"></i> Assignment</th>
                  <th><i class="fas fa-calendar"></i> Data Invio</th>
                  <th><i class="fas fa-paperclip"></i> Allegati</th>
                  <th><i class="fas fa-cog"></i> Azioni</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="submission in submissions" :key="submission.submissionId" class="submission-row">
                  <td class="assignment-cell">
                    <div class="assignment-info">
                      <span class="assignment-id">{{ submission.assignmentId }}</span>
                    </div>
                  </td>
                  <td class="date-cell">
                    <div class="date-info">
                      <span class="date">{{ formatDate(submission.submittedAt) }}</span>
                      <span class="time">{{ formatTime(submission.submittedAt) }}</span>
                    </div>
                  </td>
                  <td class="attachments-cell">
                    <div class="attachments-count">
                      <i class="fas fa-paperclip"></i>
                      <span>{{ submission.attachments.length }}</span>
                    </div>
                  </td>
                  <td class="actions-cell">
                    <button @click="viewSubmissionDetails(submission.submissionId)" class="view-btn">
                      <i class="fas fa-eye"></i>
                      Dettagli
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

export default {
  name: 'MySubmissionsList',
  setup() {
    const router = useRouter();
    const submissions = ref([]);
    const loading = ref(true);
    const error = ref(null);
    
    const getAuthHeaders = () => {
      const token = localStorage.getItem('userToken');
      return token ? { Authorization: `Bearer ${token}` } : {};
    };
    
    const fetchMySubmissions = async () => {
      try {
        const response = await axios.get('/submissions/mine', {
          headers: getAuthHeaders()
        });
        submissions.value = response.data;
      } catch (err) {
        console.error('Error fetching my submissions:', err);
        if (err.response?.status === 401) {
          error.value = 'Non autorizzato. Effettua nuovamente il login.';
        } else {
          error.value = 'Impossibile caricare le tue submission.';
        }
      } finally {
        loading.value = false;
      }
    };
    
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A';
      return new Date(dateString).toLocaleDateString('it-IT', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
      });
    };
    
    const formatTime = (dateString) => {
      if (!dateString) return 'N/A';
      return new Date(dateString).toLocaleTimeString('it-IT', {
        hour: '2-digit',
        minute: '2-digit'
      });
    };
    
    const viewSubmissionDetails = (submissionId) => {
      router.push(`/student/submissions/${submissionId}`);
    };
    
    onMounted(fetchMySubmissions);
    
    return {
      submissions, loading, error, formatDate, formatTime, viewSubmissionDetails
    };
  }
};
</script>

<style scoped>
.my-submissions-list {
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

.submissions-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  overflow: hidden;
}

.table-card {
  width: 100%;
}

.table-header {
  background: #f8f9fa;
  padding: 20px 25px;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-header h3 {
  color: #2d3436;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-header h3 i {
  color: #6c5ce7;
}

.count {
  background: #6c5ce7;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.table-content {
  padding: 0;
}

.table-responsive {
  overflow-x: auto;
}

.submissions-table {
  width: 100%;
  border-collapse: collapse;
}

.submissions-table th {
  background: #f8f9fa;
  color: #2d3436;
  font-weight: 600;
  padding: 15px 20px;
  text-align: left;
  border-bottom: 2px solid #e9ecef;
  font-size: 0.9rem;
}

.submissions-table th i {
  color: #6c5ce7;
  margin-right: 6px;
}

.submission-row {
  transition: background-color 0.3s ease;
}

.submission-row:hover {
  background: #f8f9fa;
}

.submissions-table td {
  padding: 18px 20px;
  border-bottom: 1px solid #f1f3f4;
  vertical-align: middle;
}

.assignment-cell {
  font-weight: 500;
}

.assignment-info {
  display: flex;
  flex-direction: column;
}

.assignment-id {
  color: #2d3436;
  font-weight: 600;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

.date-cell {
  min-width: 120px;
}

.date-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.date {
  color: #2d3436;
  font-weight: 500;
  font-size: 0.9rem;
}

.time {
  color: #636e72;
  font-size: 0.8rem;
}

.attachments-cell {
  text-align: center;
}

.attachments-count {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #e3f2fd;
  color: #1976d2;
  padding: 6px 12px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.85rem;
}

.attachments-count i {
  font-size: 0.8rem;
}

.actions-cell {
  text-align: center;
}

.view-btn {
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.85rem;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s ease;
}

.view-btn:hover {
  background: linear-gradient(135deg, #5a4fcf, #8b7ff0);
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .table-header {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
  
  .submissions-table {
    font-size: 0.85rem;
  }
  
  .submissions-table th,
  .submissions-table td {
    padding: 12px 8px;
  }
  
  .assignment-id {
    font-size: 0.8rem;
  }
  
  .view-btn {
    padding: 6px 12px;
    font-size: 0.8rem;
  }
}

@media (max-width: 480px) {
  .table-responsive {
    font-size: 0.8rem;
  }
  
  .submissions-table th:nth-child(3),
  .submissions-table td:nth-child(3) {
    display: none;
  }
}
</style>
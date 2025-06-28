<template>
  <div class="my-submissions-list">
    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading...</p>
    </div>

    <!-- Error -->
    <div v-if="error" class="error">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && !error && submissions.length === 0" class="empty">
      <i class="fas fa-inbox"></i>
      <h3>No Submissions</h3>
      <p>You have not submitted any submissions yet.</p>
    </div>

    <!-- Submissions Table -->
    <div v-if="!loading && !error && submissions.length > 0" class="submissions-container">
      <div class="header">
        <div class="stats">
          <span class="count">{{ submissions.length }} submission</span>
          <span> 
          
          </span>
        </div>
      </div>

      <div class="table-container">
        <table class="submissions-table">
          <thead>
            <tr>
              <th><i class="fas fa-tasks"></i> Assignment</th>
              <th><i class="fas fa-calendar-alt"></i> Date sent</th>
              <th><i class="fas fa-paperclip"></i> Attachments</th>
              <th><i class="fas fa-cog"></i> Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="submission in submissions" :key="submission.submissionId" class="submission-row">
              <td class="assignment-cell">
                <div class="assignment-info">
                  <span class="assignment-title">{{ getAssignmentTitle(submission.assignmentId) }}</span>
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
                <div class="action-buttons">
                  <button @click="viewSubmissionDetails(submission.submissionId)" class="view-btn" title="Visualizza Dettagli">
                    <i class="fas fa-eye"></i>
                    <span class="btn-label">View Details</span>
                  </button>
                  <button @click="viewSubmissionReviews(submission.submissionId)" class="reviews-btn" title="Vedi Reviews">
                    <i class="fas fa-star"></i>
                    <span class="btn-label">View Reviews</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
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
    const assignmentTitles = ref(new Map());
    
    const getAuthHeaders = () => {
      const token = localStorage.getItem('userToken');
      return token ? { Authorization: `Bearer ${token}` } : {};
    };
    
    const fetchMySubmissions = async () => {
      try {
        // Fetch submissions
        const submissionsResponse = await axios.get('/submissions/mine', {
          headers: getAuthHeaders()
        });
        submissions.value = submissionsResponse.data;
        
        // Fetch assignments titles using the student endpoint
        const assignmentsResponse = await axios.get('/assignments/student/mine', {
          headers: getAuthHeaders()
        });
        
        // Create a map of assignmentId -> title
        const titlesMap = new Map();
        assignmentsResponse.data.forEach(assignment => {
          titlesMap.set(assignment._id, assignment.title);
        });
        assignmentTitles.value = titlesMap;
        
      } catch (err) {
        error.value = 'Error fetching submissions';
        console.error('Error fetching submissions:', err);
      } finally {
        loading.value = false;
      }
    };
    
    const getAssignmentTitle = (assignmentId) => {
      return assignmentTitles.value.get(assignmentId) || assignmentId;
    };
    
    const viewSubmissionDetails = (submissionId) => {
      router.push(`/student/submissions/${submissionId}`);
    };

    const viewSubmissionReviews = (submissionId) => {
      router.push(`/student/submissions/${submissionId}/reviews`);
    };
    
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('it-IT');
    };
    
    const formatTime = (dateString) => {
      return new Date(dateString).toLocaleTimeString('it-IT', {
        hour: '2-digit',
        minute: '2-digit'
      });
    };
    
    onMounted(fetchMySubmissions);
    
    return {
      submissions,
      loading,
      error,
      getAssignmentTitle,
      viewSubmissionDetails,
      viewSubmissionReviews,
      formatDate,
      formatTime
    };
  }
};
</script>

<style scoped>
.my-submissions-list {
  padding: 0;
  max-width: 900px;
  margin: 0 auto;
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
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.12);
  overflow: hidden;
  margin-top: 24px;
  padding: 24px 18px 32px 18px;
}

/* --- MODIFICA AGGIUNTA QUI --- */
.header {
  margin-bottom: 24px; /* Aggiunge spazio sotto l'header (con il conteggio) */
}
/* --- FINE MODIFICA --- */

.table-container {
  overflow-x: auto;
}

.submissions-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 700px;
}

.submissions-table th, .submissions-table td {
  padding: 16px 14px;
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

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-start;
}

.view-btn, .reviews-btn {
  padding: 8px 18px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 500;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-label {
  display: inline-block;
  margin-left: 4px;
}

@media (max-width: 900px) {
  .my-submissions-list {
    max-width: 100%;
    padding: 0 4px;
  }
  .submissions-container {
    padding: 12px 2px 18px 2px;
  }
  .submissions-table {
    min-width: 500px;
  }
}

@media (max-width: 600px) {
  .submissions-table th, .submissions-table td {
    padding: 10px 4px;
    font-size: 0.85rem;
  }
  .view-btn, .reviews-btn {
    padding: 6px 8px;
    font-size: 0.85rem;
  }
  .btn-label {
    display: none;
  }
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

.assignment-title {
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.95rem;
}

@media (max-width: 768px) {
  .assignment-title {
    font-size: 0.85rem;
  }
}
</style>
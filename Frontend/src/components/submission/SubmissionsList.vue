<template>
  <div class="submissions-list">
    <div class="header-section">
      <div class="header-content">
        <h2><i class="fas fa-file-alt"></i> Submissions</h2>
        <div class="assignment-info">
          <h3>{{ assignmentTitle }}</h3>
          <div class="stats">
            <div class="stat-item">
              <i class="fas fa-users"></i>
              <span>{{ submissions.length }} submissions</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Caricamento submissions...</p>
    </div>
    
    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-triangle"></i>
      {{ error }}
    </div>
    
    <div v-if="!loading && !error && submissions.length === 0" class="no-submissions">
      <i class="fas fa-inbox"></i>
      <h4>Nessuna Submission</h4>
      <p>Non ci sono ancora submissions per questo assignment.</p>
    </div>
    
    <div v-if="!loading && !error && submissions.length > 0" class="submissions-container">
      <div class="submissions-grid">
        <div v-for="submission in submissions" :key="submission.submissionId" class="submission-card">
          <div class="card-header">
            <div class="student-info">
              <div class="student-avatar">
                {{ getInitials(submission.studentName, submission.studentSurname) }}
              </div>
              <div class="student-details">
                <h4>{{ submission.studentName }} {{ submission.studentSurname }}</h4>
                <p class="student-id">ID: {{ submission.studentSerialNumber || 'N/A' }}</p>
              </div>
            </div>
            <div class="submission-status">
              <span class="status-badge submitted">
                <i class="fas fa-check-circle"></i>
                Submitted
              </span>
            </div>
          </div>
          
          <div class="card-body">
            <div class="submission-meta">
              <div class="meta-row">
                <div class="meta-item">
                  <i class="fas fa-calendar-alt"></i>
                  <span>{{ formatDate(submission.submittedAt) }}</span>
                </div>
                <div class="meta-item">
                  <i class="fas fa-paperclip"></i>
                  <span>{{ submission.attachments.length }} allegati</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="card-actions">
            <button @click="viewSubmissionDetails(submission.submissionId)" class="view-details-btn">
              <i class="fas fa-eye"></i>
              Visualizza Dettagli
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

export default {
  name: 'SubmissionsList',
  setup() {
    const route = useRoute();
    const router = useRouter();
    const assignmentId = ref(route.params.assignmentId);
    const assignmentTitle = ref('');
    const submissions = ref([]);
    const loading = ref(true);
    const error = ref(null);
    
    const getAuthHeaders = () => {
      const token = localStorage.getItem('userToken');
      return token ? { Authorization: `Bearer ${token}` } : {};
    };
    
    const fetchAssignmentDetails = async () => {
      try {
        const response = await axios.get(`/assignments/${assignmentId.value}`, {
          headers: getAuthHeaders()
        });
        assignmentTitle.value = response.data.title;
      } catch (err) {
        console.error('Error fetching assignment details:', err);
        error.value = 'Impossibile caricare i dettagli dell\'assignment.';
      }
    };
    
    const fetchSubmissions = async () => {
      try {
        const response = await axios.get(`/submissions/assignment/${assignmentId.value}`, {
          headers: getAuthHeaders()
        });
        submissions.value = response.data;
      } catch (err) {
        console.error('Error fetching submissions:', err);
        if (err.response && err.response.status === 403) {
          error.value = 'Non sei autorizzato a visualizzare queste submissions.';
        } else {
          error.value = 'Impossibile caricare le submissions. Riprova più tardi.';
        }
      } finally {
        loading.value = false;
      }
    };
    
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A';
      const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
      return new Date(dateString).toLocaleDateString(undefined, options);
    };
    
    const viewSubmissionDetails = (submissionId) => {
      router.push(`/teacher/assignments/${assignmentId.value}/submissions/${submissionId}`);
    };
    
    onMounted(async () => {
      await fetchAssignmentDetails();
      await fetchSubmissions();
    });
    
    // Aggiungi questa nuova funzione
    const getInitials = (firstName, lastName) => {
      return `${firstName?.charAt(0) || ''}${lastName?.charAt(0) || ''}`.toUpperCase();
    };
    
    return {
      assignmentId,
      assignmentTitle,
      submissions,
      loading,
      error,
      formatDate,
      viewSubmissionDetails,
      getInitials // Aggiungi questa funzione al return
    };
  }
};
</script>

<style scoped>
.submissions-list {
  padding: 24px;
  background-color: #f8f9fa;
  min-height: 100vh;
}

.header-section {
  margin-bottom: 32px;
  padding: 24px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.header-content {
  text-align: center;
}

.header-content h2 {
  font-size: 2.5rem;
  margin: 0 0 16px 0;
  font-weight: 700;
  color: #2c3e50;
}

.header-content h2 i {
  color: #3498db;
  margin-right: 12px;
}

.assignment-info h3 {
  font-size: 1.5rem;
  margin: 0 0 16px 0;
  color: #495057;
}

.stats {
  display: flex;
  justify-content: center;
  gap: 24px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #e3f2fd;
  color: #1976d2;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 500;
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

.no-submissions {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  color: #6c757d;
}

.no-submissions i {
  font-size: 4rem;
  margin-bottom: 16px;
  color: #dee2e6;
}

.no-submissions h4 {
  font-size: 1.5rem;
  margin: 0 0 8px 0;
  color: #495057;
}

.submissions-container {
  max-width: 1200px;
  margin: 0 auto;
}

.submissions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
}

.submission-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  transition: all 0.3s ease;
  border: 1px solid #e9ecef;
}

.submission-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.card-header {
  padding: 20px;
  border-bottom: 1px solid #f8f9fa;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.student-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.student-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3498db, #2980b9);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1.1rem;
}

.student-details h4 {
  margin: 0 0 4px 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
}

.student-id {
  margin: 0;
  font-size: 0.85rem;
  color: #6c757d;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-badge.submitted {
  background: #d4edda;
  color: #155724;
}

.card-body {
  padding: 16px 20px;
}

.submission-meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meta-row {
  display: flex;
  gap: 20px;
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
}

.view-details-btn {
  width: 100%;
  padding: 12px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.view-details-btn:hover {
  background: #2980b9;
  transform: translateY(-1px);
}
</style>
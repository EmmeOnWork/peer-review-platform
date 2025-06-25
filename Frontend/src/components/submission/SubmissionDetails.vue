<template>
  <div class="submission-details">
    <!-- Header compatto -->
    <div class="header">
      <button @click="goBack" class="back-btn">
        <i class="fas fa-arrow-left"></i>
      </button>
      <h1>Dettagli Submission</h1>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <i class="fas fa-spinner fa-spin"></i>
      <span>Caricamento...</span>
    </div>

    <!-- Error -->
    <div v-if="error" class="error">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
      <button @click="fetchSubmissionDetails" class="retry-btn">Riprova</button>
    </div>
    
    <!-- Content -->
    <div v-if="!loading && !error && submission" class="content">
      <!-- Studente -->
      <div class="card student">
        <i class="fas fa-user"></i>
        <div class="info">
          <h2>{{ submission.studentName }} {{ submission.studentSurname }}</h2>
          <span>{{ submission.studentSerialNumber }}</span>
        </div>
        <span class="badge">Consegnato</span>
      </div>

      <!-- Info generali -->
      <div class="card">
        <h3><i class="fas fa-info-circle"></i> Informazioni</h3>
        <div class="grid">
          <div class="item">
            <i class="fas fa-calendar"></i>
            <div>
              <span class="label">Data</span>
              <span class="value">{{ formatDate(submission.submittedAt) }}</span>
            </div>
          </div>
          <div class="item">
            <i class="fas fa-clock"></i>
            <div>
              <span class="label">Ora</span>
              <span class="value">{{ formatTime(submission.submittedAt) }}</span>
            </div>
          </div>
        </div>
      </div>
        
      <!-- Testo -->
      <div class="card" v-if="submission.text">
        <h3><i class="fas fa-file-alt"></i> Testo</h3>
        <div class="text">{{ submission.text }}</div>
      </div>
        
      <!-- Allegati -->
      <div class="card">
        <h3><i class="fas fa-paperclip"></i> Allegati</h3>
        <div v-if="submission.attachments?.length" class="attachments">
          <div v-for="(attachment, index) in submission.attachments" :key="index" class="attachment">
            <i class="fas" :class="getFileIcon(attachment)"></i>
            <span>{{ getFileName(attachment) }}</span>
            <button @click="downloadAttachment(attachment)" class="download">
              <i class="fas fa-download"></i>
            </button>
          </div>
        </div>
        <div v-else class="empty">
          <i class="fas fa-folder-open"></i>
          <span>Nessun allegato</span>
        </div>
      </div>
      
      <!-- Peer Review Section (solo per teacher) -->
      <div class="card" v-if="userRole === 'teacher'">
        <h3><i class="fas fa-users"></i> Peer Review</h3>
        <div class="review-actions">
          <button @click="openAutoAssignModal" class="btn btn-primary">
            <i class="fas fa-magic"></i>
            Assegnazione Automatica
          </button>
          <button @click="openManualAssignModal" class="btn btn-secondary">
            <i class="fas fa-hand-pointer"></i>
            Assegnazione Manuale
          </button>
        </div>
      </div>
      
      <!-- Modal per Assegnazione Automatica -->
      <div v-if="showAutoModal" class="modal-overlay" @click="closeModals">
        <div class="modal" @click.stop>
          <div class="modal-header">
            <h3>Assegnazione Automatica Peer Review</h3>
            <button @click="closeModals" class="close-btn">&times;</button>
          </div>
          <div class="modal-body">
            <p>Seleziona a quanti studenti assegnare questa submission per la review:</p>
            <div class="input-group">
              <label for="reviewCount">Numero di reviewer:</label>
              <input 
                id="reviewCount" 
                v-model.number="autoAssignData.minReviews" 
                type="number" 
                min="1" 
                max="10" 
                class="form-control"
              >
            </div>
          </div>
          <div class="modal-footer">
            <button @click="closeModals" class="btn btn-cancel">Annulla</button>
            <button @click="submitAutoAssign" class="btn btn-primary" :disabled="autoAssignLoading">
              <i v-if="autoAssignLoading" class="fas fa-spinner fa-spin"></i>
              Assegna Automaticamente
            </button>
          </div>
        </div>
      </div>
      
      <!-- Modal per Assegnazione Manuale -->
      <div v-if="showManualModal" class="modal-overlay" @click="closeModals">
        <div class="modal" @click.stop>
          <div class="modal-header">
            <h3>Assegnazione Manuale Peer Review</h3>
            <button @click="closeModals" class="close-btn">&times;</button>
          </div>
          <div class="modal-body">
            <p>Seleziona gli studenti che dovranno revieware questa submission:</p>
            <div v-if="studentsLoading" class="loading">
              <i class="fas fa-spinner fa-spin"></i> Caricamento studenti...
            </div>
            <div v-else class="students-list">
              <div 
                v-for="student in availableStudents" 
                :key="student.serialNumber"
                class="student-item"
              >
                <input 
                  :id="`student-${student.serialNumber}`"
                  v-model="manualAssignData.selectedStudents"
                  :value="student.serialNumber"
                  type="checkbox"
                  class="student-checkbox"
                >
                <label :for="`student-${student.serialNumber}`" class="student-label">
                  <div class="student-info">
                    <span class="student-name">{{ student.name }} {{ student.surname }}</span>
                    <span class="student-serial">{{ student.serialNumber }}</span>
                  </div>
                </label>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button @click="closeModals" class="btn btn-cancel">Annulla</button>
            <button 
              @click="submitManualAssign" 
              class="btn btn-primary" 
              :disabled="manualAssignLoading || manualAssignData.selectedStudents.length === 0"
            >
              <i v-if="manualAssignLoading" class="fas fa-spinner fa-spin"></i>
              Assegna a {{ manualAssignData.selectedStudents.length }} studenti
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
import reviewService from '@/services/reviewService';

export default {
  name: 'SubmissionDetails',
  setup() {
    const route = useRoute();
    const router = useRouter();
    const submissionId = ref(route.params.submissionId);
    const assignmentId = ref(route.params.assignmentId); // Prendo assignmentId dai params della route
    const submission = ref(null);
    const loading = ref(true);
    const error = ref(null);
    
    // User role
    const userRole = ref(localStorage.getItem('userRole'));
    
    // Modal states
    const showAutoModal = ref(false);
    const showManualModal = ref(false);
    const autoAssignLoading = ref(false);
    const manualAssignLoading = ref(false);
    const studentsLoading = ref(false);
    
    // Data for assignments
    const autoAssignData = ref({
      minReviews: 2
    });
    
    const manualAssignData = ref({
      selectedStudents: []
    });
    
    const availableStudents = ref([]);
    
    const getAuthHeaders = () => {
      const token = localStorage.getItem('userToken');
      return token ? { Authorization: `Bearer ${token}` } : {};
    };
    
    const fetchSubmissionDetails = async () => {
      loading.value = true;
      error.value = null;
      try {
        const response = await axios.get(`/submissions/${submissionId.value}`, {
          headers: getAuthHeaders()
        });
        submission.value = response.data;
        // Se l'assignmentId non è nei params della route, lo prendo dalla submission
        if (!assignmentId.value && submission.value.assignmentId) {
          assignmentId.value = submission.value.assignmentId;
        }
      } catch (err) {
        console.error('Error fetching submission details:', err);
        if (err.response?.status === 403) {
          error.value = 'Non autorizzato.';
        } else if (err.response?.status === 404) {
          error.value = 'Submission non trovata.';
        } else {
          error.value = 'Errore di caricamento.';
        }
      } finally {
        loading.value = false;
      }
    };
    
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A';
      return new Date(dateString).toLocaleDateString('it-IT');
    };

    const formatTime = (dateString) => {
      if (!dateString) return 'N/A';
      return new Date(dateString).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' });
    };
    
    const getFileName = (path) => {
      if (!path) return 'File sconosciuto';
      return path.split('/').pop();
    };

    const getFileIcon = (path) => {
      const ext = getFileName(path).split('.').pop()?.toLowerCase();
      const icons = {
        'pdf': 'fa-file-pdf',
        'doc': 'fa-file-word', 'docx': 'fa-file-word',
        'xls': 'fa-file-excel', 'xlsx': 'fa-file-excel',
        'jpg': 'fa-file-image', 'jpeg': 'fa-file-image', 'png': 'fa-file-image',
        'zip': 'fa-file-archive', 'rar': 'fa-file-archive'
      };
      return icons[ext] || 'fa-file';
    };
    
    const downloadAttachment = async (attachmentPath) => {
      try {
        const pathParts = attachmentPath.split('/');
        const [, studentId, assignmentId, filename] = pathParts;
        
        const response = await axios.get(`/submissions/download/${studentId}/${assignmentId}/${filename}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('userToken')}` },
          responseType: 'blob'
        });
        
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('Download error:', error);
        alert('Errore download');
      }
    };
    
    // Modal functions
    const openAutoAssignModal = () => {
      showAutoModal.value = true;
    };
    
    const openManualAssignModal = async () => {
      showManualModal.value = true;
      await fetchAvailableStudents();
    };
    
    const closeModals = () => {
      showAutoModal.value = false;
      showManualModal.value = false;
      manualAssignData.value.selectedStudents = [];
    };
    
    // Fetch available students (excluding the author)
    const fetchAvailableStudents = async () => {
      if (!assignmentId.value) {
        console.error('Assignment ID not available');
        alert('ID Assignment non disponibile');
        return;
      }
      
      studentsLoading.value = true;
      try {
        const students = await reviewService.getAssignmentStudents(assignmentId.value);
        // Exclude the submission author from available reviewers
        availableStudents.value = students.filter(student => 
          student.serialNumber !== submission.value.studentSerialNumber
        );
      } catch (err) {
        console.error('Error fetching students:', err);
        alert('Errore nel caricamento degli studenti');
      } finally {
        studentsLoading.value = false;
      }
    };
    
    // Submit auto assignment
    const submitAutoAssign = async () => {
      autoAssignLoading.value = true;
      try {
        const response = await reviewService.assignAutoReview(
          assignmentId.value,
          autoAssignData.value.minReviews
        );
        
        alert(`Assegnazione automatica completata! Create ${response.length} review.`);
        closeModals();
      } catch (error) {
        console.error('Error in auto assignment:', error);
        alert('Errore nell\'assegnazione automatica');
      } finally {
        autoAssignLoading.value = false;
      }
    };
    
    // Submit manual assignment
    const submitManualAssign = async () => {
      manualAssignLoading.value = true;
      try {
        const manualAssignments = manualAssignData.value.selectedStudents.map(studentSerial => ({
          submissionId: submissionId.value,
          reviewerserialNumber: studentSerial  // Changed from reviewerSerialNumber to reviewerserialNumber
        }));
        
        const response = await reviewService.assignManualReview(
          assignmentId.value,
          manualAssignments
        );
        
        alert(`Assegnazione manuale completata! Create ${response.length} review.`);
        closeModals();
      } catch (error) {
        console.error('Error in manual assignment:', error);
        alert('Errore nell\'assegnazione manuale');
      } finally {
        manualAssignLoading.value = false;
      }
    };
    
    const goBack = () => router.go(-1);
    
    onMounted(fetchSubmissionDetails);
    
    return {
      submission, loading, error, formatDate, formatTime,
      getFileName, getFileIcon, downloadAttachment, goBack, fetchSubmissionDetails,
      userRole, showAutoModal, showManualModal, autoAssignLoading, manualAssignLoading,
      studentsLoading, autoAssignData, manualAssignData, availableStudents,
      openAutoAssignModal, openManualAssignModal, closeModals,
      submitAutoAssign, submitManualAssign
    };
  }
};
</script>

<style scoped>
.submission-details {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  background: #f8f9fa;
  min-height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.back-btn {
  width: 40px;
  height: 40px;
  background: #6c5ce7;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-btn:hover {
  background: #5a4fcf;
}

.header h1 {
  margin: 0;
  color: #2d3436;
  font-size: 1.5rem;
}

.loading, .error {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px;
  background: white;
  border-radius: 8px;
  text-align: center;
}

.loading i {
  font-size: 1.5rem;
  color: #6c5ce7;
}

.error {
  flex-direction: column;
}

.error i {
  font-size: 2rem;
  color: #e74c3c;
}

.retry-btn {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.card.student {
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  color: white;
  display: flex;
  align-items: center;
  gap: 15px;
}

.card.student i {
  font-size: 2rem;
  background: rgba(255,255,255,0.2);
  padding: 15px;
  border-radius: 50%;
}

.card.student .info {
  flex: 1;
}

.card.student h2 {
  margin: 0 0 5px 0;
  font-size: 1.3rem;
}

.badge {
  background: rgba(255,255,255,0.2);
  padding: 5px 12px;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: bold;
}

.card h3 {
  margin: 0 0 15px 0;
  color: #2d3436;
  display: flex;
  align-items: center;
  gap: 8px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.item i {
  color: #6c5ce7;
  font-size: 1.2rem;
}

.label {
  display: block;
  font-size: 0.8rem;
  color: #636e72;
  text-transform: uppercase;
}

.value {
  display: block;
  font-weight: bold;
  color: #2d3436;
}

.text {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  border-left: 3px solid #6c5ce7;
  white-space: pre-wrap;
  line-height: 1.5;
}

.attachments {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.attachment {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #ddd;
}

.attachment i {
  color: #6c5ce7;
  font-size: 1.2rem;
}

.attachment span {
  flex: 1;
  font-weight: 500;
}

.download {
  background: #00b894;
  color: white;
  border: none;
  padding: 6px 10px;
  border-radius: 4px;
  cursor: pointer;
}

.download:hover {
  background: #00a085;
}

.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 30px;
  color: #636e72;
  font-style: italic;
}

.empty i {
  font-size: 1.5rem;
}

/* Peer Review Styles */
.review-actions {
  display: flex;
  gap: 15px;
  margin-top: 15px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #545b62;
}

.btn-cancel {
  background: #dc3545;
  color: white;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid #dee2e6;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6c757d;
}

.input-group {
  margin: 15px 0;
}

.input-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
}

.students-list {
  max-height: 300px;
  overflow-y: auto;
}

.student-item {
  display: flex;
  align-items: center;
  padding: 10px;
  border: 1px solid #dee2e6;
  border-radius: 5px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.student-item:hover {
  background-color: #f8f9fa;
}

.student-checkbox {
  margin-right: 12px;
}

.student-label {
  flex: 1;
  cursor: pointer;
}

.student-info {
  display: flex;
  flex-direction: column;
}

.student-name {
  font-weight: 500;
  color: #333;
}

.student-serial {
  font-size: 0.9em;
  color: #6c757d;
}

@media (max-width: 768px) {
  .submission-details {
    padding: 10px;
  }
  
  .grid {
    grid-template-columns: 1fr;
  }
  
  .card.student {
    flex-direction: column;
    text-align: center;
  }
  
  .review-actions {
    flex-direction: column;
  }
}
</style>
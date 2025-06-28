<template>
  <div class="teacher-reports-page">
    <div class="header-section">
      <h1><i class="fas fa-chart-bar"></i> Assignment Reports</h1>
      <p>View detailed reports of your assignments</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <i class="fas fa-spinner fa-spin"></i>
      <span>Loading report...</span>
    </div>

    <!-- Error -->
    <div v-if="error" class="error">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>

    <!-- Reports Grid -->
    <div v-if="!loading && !error && reports.length > 0" class="reports-grid">
      <div v-for="report in reports" :key="report.assignmentId" class="report-card">
        <!-- Card Header -->
        <div class="card-header" @click="toggleCard(report.assignmentId)">
          <div class="assignment-info">
            <h3>{{ report.title }}</h3>
          </div>
          <div class="expand-icon" :class="{ 'expanded': expandedCards.includes(report.assignmentId) }">
            <i class="fas fa-chevron-down"></i>
          </div>
        </div>

        <!-- Average Scores Summary -->
        <div class="card-summary">
          <h4><i class="fas fa-chart-line"></i> Average Scores per Criterion</h4>
          <div class="scores-grid">
            <div v-for="score in report.averageScores" :key="score.criterion" class="score-item">
              <span class="criterion">{{ score.criterion }}</span>
              <span class="score" :class="getScoreClass(score.averageScore)">{{ score.averageScore.toFixed(1) }}</span>
            </div>
          </div>
        </div>

        <!-- Expandable Content -->
        <div v-if="expandedCards.includes(report.assignmentId)" class="card-details">
          <div class="submissions-section">
            <h4><i class="fas fa-users"></i> Student Submissions ({{ report.submissions.length }})</h4>
            
            <div v-for="submission in report.submissions" :key="submission.submissionId" class="submission-item">
              <div class="submission-header">
                <div class="student-info">
                  <span class="student-name">{{ getStudentName(submission.serialNumber) }}</span>
                  <span class="student-serial">({{ submission.serialNumber }})</span>
                </div>
              </div>

              <!-- Student Average Scores -->
              <div class="student-scores">
                <h5>Average Scores:</h5>
                <div class="scores-row">
                  <span v-for="score in submission.averageScores" :key="score.criterion" 
                        class="score-badge" :class="getScoreClass(score.averageScore)">
                    {{ score.criterion }}: {{ score.averageScore.toFixed(1) }}
                  </span>
                </div>
              </div>

              <!-- Peer Reviews -->
              <div class="peer-reviews">
                <h5>Peer Reviews ({{ submission.peerReviews.length }}):</h5>
                <div v-for="review in submission.peerReviews" :key="review.reviewerSerialNumber" class="review-item">
                  <div class="review-header">
                    <span class="reviewer">Reviewer: {{ getStudentName(review.reviewerSerialNumber) }} ({{ review.reviewerSerialNumber }})</span>
                    <span class="review-date">{{ formatDate(review.reviewedAt) }}</span>
                  </div>
                  <div class="review-scores">
                    <div v-for="val in review.evaluation" :key="val.criterion" class="criterion-review">
                      <span class="criterion-name">{{ val.criterion }}</span>
                      <span class="criterion-score" :class="getScoreClass(val.score)">{{ val.score }}</span>
                      <p class="feedback" v-if="val.feedback">{{ val.feedback }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && !error && reports.length === 0" class="empty">
      <i class="fas fa-chart-bar"></i>
      <h3>Nessun Report Disponibile</h3>
      <p>Non ci sono ancora report per i tuoi assignment.</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useStore } from 'vuex';
import reportService from '@/services/reportService';
import authService from '@/services/authService'; // Aggiungi questo import

export default {
  name: 'TeacherReportsPage',
  setup() {
    const store = useStore();
    const reports = ref([]);
    const loading = ref(true);
    const error = ref(null);
    const studentsMap = ref(new Map()); // Mappa per cachare i dati degli studenti

    const user = computed(() => store.state.user);

    // Funzione per ottenere i dettagli degli studenti
    const loadStudentsDetails = async () => {
      try {
        const allStudents = await authService.getAllStudents();
        const studentsMapTemp = new Map();
        
        allStudents.forEach(student => {
          studentsMapTemp.set(student.serialNumber, {
            name: student.name,
            surname: student.surname,
            serialNumber: student.serialNumber
          });
        });
        
        studentsMap.value = studentsMapTemp;
      } catch (error) {
        console.error('Error loading students details:', error);
      }
    };

    const fetchReports = async () => {
      try {
        loading.value = true;
        error.value = null;
        
        const userSerialNumber = user.value?.serialNumber;
        if (!userSerialNumber) {
          throw new Error('Serial number dell\'insegnante non trovato');
        }

        const data = await reportService.getTeacherReports(userSerialNumber);
        reports.value = data;
        
        // Carica i dettagli degli studenti dopo aver ottenuto i report
        await loadStudentsDetails();
      } catch (err) {
        console.error('Error fetching reports:', err);
        error.value = err.response?.data?.error || 'Error loading reports';
      } finally {
        loading.value = false;
      }
    };

    // Funzione helper per ottenere nome e cognome dello studente
    const getStudentName = (serialNumber) => {
      const student = studentsMap.value.get(serialNumber);
      return student ? `${student.name} ${student.surname}` : serialNumber;
    };

    const expandedCards = ref([]);

    const toggleCard = (assignmentId) => {
      const index = expandedCards.value.indexOf(assignmentId);
      if (index > -1) {
        expandedCards.value.splice(index, 1);
      } else {
        expandedCards.value.push(assignmentId);
      }
    };

    const getScoreClass = (score) => {
      if (score >= 80) return 'excellent';
      if (score >= 60) return 'good';
      if (score >= 40) return 'fair';
      return 'poor';
    };

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('it-IT', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    };

    onMounted(fetchReports);

    return {
      reports,
      loading,
      error,
      expandedCards,
      studentsMap,
      toggleCard,
      getScoreClass,
      formatDate,
      getStudentName // Aggiungi questa funzione al return
    };
  }
};
</script>

<style scoped>
.teacher-reports-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  background: #f8f9fa;
  min-height: 100vh;
}

.header-section {
  text-align: center;
  margin-bottom: 30px;
}

.header-section h1 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.header-section h1 i {
  color: #9B59B6;
  margin-right: 10px;
}

.loading, .error, .empty {
  text-align: center;
  padding: 40px;
  border-radius: 8px;
  margin: 20px 0;
}

.loading {
  background: #f8f9fa;
  color: #6c757d;
}

.error {
  background: #f8d7da;
  color: #721c24;
}

.empty {
  background: #e2e3e5;
  color: #383d41;
}

.reports-grid {
  display: grid;
  gap: 20px;
}

.report-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  overflow: hidden;
  transition: all 0.3s ease;
}

.report-card:hover {
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

.card-header {
  background: linear-gradient(135deg, #9B59B6, #8E44AD);
  color: white;
  padding: 20px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.assignment-info h3 {
  margin: 0;
  font-size: 1.3rem;
}



.expand-icon {
  transition: transform 0.3s ease;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.card-summary {
  padding: 20px;
}

.scores-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.score-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.criterion {
  font-weight: 500;
  color: #495057;
}

.score {
  font-weight: bold;
  padding: 4px 8px;
  border-radius: 4px;
  color: white;
}

.score.excellent { background: #28a745; }
.score.good { background: #17a2b8; }
.score.fair { background: #ffc107; color: #212529; }
.score.poor { background: #dc3545; }

.card-details {
  border-top: 1px solid #dee2e6;
  padding: 20px;
  background: #f8f9fa;
}

.submission-item {
  background: white;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  border-left: 4px solid #9B59B6;
}

.submission-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.student-name {
  font-weight: bold;
  color: #2c3e50;
  font-size: 1.1rem;
}

.student-serial {
  font-size: 0.9rem;
  color: #6c757d;
  margin-left: 8px;
}
/*
.submission-id {
  font-size: 0.8rem;
  color: #6c757d;
  margin-left: 10px;
}*/

.student-scores, .peer-reviews {
  margin-top: 15px;
}

.scores-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.score-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgb(0, 2, 3);
}

.review-item {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 10px;
}

.review-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.reviewer {
  font-weight: 500;
  color: #495057;
}

.review-date {
  color: #6c757d;
}

.criterion-review {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

.criterion-name {
  font-weight: 500;
  min-width: 100px;
}

.criterion-score {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.8rem;
  font-weight: bold;
  color: rgb(0, 0, 0);
}

.feedback {
  margin: 5px 0 0 110px;
  font-style: italic;
  color: #6c757d;
  font-size: 0.9rem;
}
</style>
<template>
  <div class="submission-reviews-page">
    <div class="header-section">
      <button @click="goBack" class="back-btn">
        <i class="fas fa-arrow-left"></i>
        Back to Submissions
      </button>
      <h1><i class="fas fa-star"></i> Reviews for Your Submission</h1>
      <p v-if="reviewData">{{ reviewData.title }}</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <i class="fas fa-spinner fa-spin"></i>
      <span>Loading reviews...</span>
    </div>

    <!-- Error -->
    <div v-if="error" class="error">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>

    <!-- Reviews Content -->
    <div v-if="!loading && !error && reviewData" class="reviews-content">
      <!-- Summary Card -->
      <div class="summary-card">
        <h3><i class="fas fa-chart-line"></i> Summary</h3>
        <div class="summary-info">

          <div class="info-item">
            <span class="label">Assignment:</span>
            <span class="value">{{ reviewData.title }}</span>
          </div>
          <div class="info-item">
            <span class="label">Number of Reviews:</span>
            <span class="value">{{ reviewData.reviews.length }}</span>
          </div>
          <div class="info-item">
            <span class="label">Average Score:</span>
            <span class="value score" :class="getScoreClass(reviewData.averageScore)">{{ reviewData.averageScore.toFixed(1) }}</span>
          </div>
        </div>
      </div>

      <!-- Reviews List -->
      <div class="reviews-list">
        <h3><i class="fas fa-comments"></i> Reviews Received ({{ reviewData.reviews.length }})</h3>
        
        <div v-if="reviewData.reviews.length === 0" class="no-reviews">
          <i class="fas fa-inbox"></i>
          <h4>No Reviews</h4>
          <p>You have not received any reviews for this submission yet.</p>
        </div>

        <div v-for="(review, index) in reviewData.reviews" :key="index" class="review-card">
          <div class="review-header">
            <div class="review-info">
              <span class="review-number">Review #{{ index + 1 }}</span>
              <span class="review-date">{{ formatDate(review.reviewedAt) }}</span>
            </div>
          </div>

          <div class="review-content">
            <h4><i class="fas fa-list-check"></i> Scores by Criterion</h4>
            <div class="criteria-list">
              <div v-if="review.evaluation && review.evaluation.length > 0" class="mb-3">
                <h6>Scores:</h6>
                <div v-for="val in review.evaluation" :key="val.criterion" class="mb-2">
                  <div class="criterion-header">
                    <span class="criterion-name">{{ val.criterion }}</span>
                    <span class="criterion-score" :class="getScoreClass(val.score)">{{ val.score }}</span>
                  </div>
                  <div v-if="val.feedback" class="criterion-feedback">
                    <i class="fas fa-comment"></i>
                    <p>{{ val.feedback }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useStore } from 'vuex';
import reportService from '@/services/reportService';

export default {
  name: 'SubmissionReviewsPage',
  setup() {
    const route = useRoute();
    const router = useRouter();
    const store = useStore();
    const reviewData = ref(null);
    const loading = ref(true);
    const error = ref(null);

    const user = computed(() => store.state.user);

    const fetchReviews = async () => {
      try {
        const submissionId = route.params.submissionId;
        const userSerialNumber = user.value?.serialNumber;
        
        if (!userSerialNumber) {
          throw new Error('Serial number dello studente non trovato');
        }
        
        const data = await reportService.getStudentSubmissionReviews(userSerialNumber, submissionId);
        reviewData.value = data;
      } catch (err) {
        error.value = 'Error loading reviews';
        console.error('Error fetching reviews:', err);
      } finally {
        loading.value = false;
      }
    };

    const goBack = () => {
      router.push('/student/submissions');
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
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    };

    onMounted(fetchReviews);

    return {
      reviewData,
      loading,
      error,
      goBack,
      getScoreClass,
      formatDate
    };
  }
};
</script>

<style scoped>
.submission-reviews-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  background: #f8f9fa;
  min-height: 100vh;
}

.header-section {
  margin-bottom: 30px;
}

.back-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.3s ease;
}

.back-btn:hover {
  background: #5a6268;
}

.header-section h1 {
  color: #2c3e50;
  margin: 10px 0;
}

.header-section h1 i {
  color: #9B59B6;
  margin-right: 10px;
}

.loading, .error {
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

.summary-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.summary-card h3 {
  color: #2c3e50;
  margin-bottom: 15px;
}

.summary-card h3 i {
  color: #9B59B6;
  margin-right: 8px;
}

.summary-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
}

.label {
  font-weight: 500;
  color: #495057;
}

.value {
  font-weight: 600;
  color: #2c3e50;
}

.value.score {
  padding: 4px 8px;
  border-radius: 4px;
  color: white;
}

.score.excellent { background: #28a745; }
.score.good { background: #17a2b8; }
.score.fair { background: #ffc107; color: #212529; }
.score.poor { background: #dc3545; }

.reviews-list {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.reviews-list h3 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.reviews-list h3 i {
  color: #9B59B6;
  margin-right: 8px;
}

.no-reviews {
  text-align: center;
  padding: 40px;
  color: #6c757d;
}

.no-reviews i {
  font-size: 3rem;
  margin-bottom: 15px;
  color: #dee2e6;
}

.review-card {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  margin-bottom: 20px;
  overflow: hidden;
}

.review-header {
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  padding: 15px 20px;
  border-bottom: 1px solid #dee2e6;
}

.review-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.review-number {
  font-weight: 600;
  color: #495057;
}

.review-date {
  color: #6c757d;
  font-size: 0.9rem;
}

.review-content {
  padding: 20px;
}

.review-content h4 {
  color: #495057;
  margin-bottom: 15px;
}

.review-content h4 i {
  color: #9B59B6;
  margin-right: 8px;
}

.criteria-list {
  display: grid;
  gap: 15px;
}

.criterion-item {
  border-left: 4px solid #9B59B6;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 0 6px 6px 0;
}

.criterion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.criterion-name {
  font-weight: 600;
  color: #2c3e50;
}

.criterion-score {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: bold;
  color: black;
  font-size: 0.9rem;
}

.criterion-feedback {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 10px;
}

.criterion-feedback i {
  color: #9B59B6;
  margin-top: 2px;
}

.criterion-feedback p {
  margin: 0;
  color: #495057;
  font-style: italic;
  line-height: 1.4;
}

@media (max-width: 768px) {
  .summary-info {
    grid-template-columns: 1fr;
  }
  
  .criterion-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .review-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
}
</style>
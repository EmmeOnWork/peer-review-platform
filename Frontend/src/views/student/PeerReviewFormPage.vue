<template>
  <div class="peer-review-form-page">
    <!-- Loading -->
    <div v-if="loading" class="loading">
      <i class="fas fa-spinner fa-spin"></i>
      <span>Loading...</span>
    </div>

    <!-- Error -->
    <div v-if="error" class="error">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
      <button @click="$router.go(-1)" class="back-btn">
        <i class="fas fa-arrow-left"></i> Go Back
      </button>
    </div>

    <!-- Main Content -->
    <div v-if="!loading && !error" class="content">
      <!-- Header -->
      <div class="header-section">
        <button @click="$router.go(-1)" class="back-btn">
          <i class="fas fa-arrow-left"></i> Back to Peer Reviews
        </button>
        <h1>
          <i class="fas fa-star"></i>
          {{ isCompleted ? 'View' : 'Complete' }} Peer Review
        </h1>
      </div>

      <!-- Submission Details Section -->
      <div class="submission-section">
        <div class="section-header">
          <h2><i class="fas fa-file-alt"></i> Submission to Review</h2>
        </div>
        
        <div class="submission-card">
          <div class="submission-info">
            <div class="info-row">
            </div>
            <div class="info-row">
              <span class="label">Assignment:</span>
              <span class="value">{{ reviewData?.assignmentId }}</span>
            </div>
            <div class="info-row">
              <span class="label">Submission Date:</span>
              <span class="value">{{ formatDate(submissionData?.submittedAt) }}</span>
            </div>
          </div>

          <!-- Submission Text -->
          <div v-if="submissionData?.text" class="submission-text">
            <h4>Submission Text:</h4>
            <div class="text-content">{{ submissionData.text }}</div>
          </div>

          <!-- Attachments -->
          <div v-if="submissionData?.attachments?.length > 0" class="attachments-section">
            <h4><i class="fas fa-paperclip"></i> Attachments ({{ submissionData.attachments.length }}):</h4>
            <div class="attachments-list">
              <div 
                v-for="attachment in submissionData.attachments" 
                :key="attachment.originalName"
                class="attachment-item"
              >
                <div class="attachment-info">
                  <i class="fas fa-file"></i>
                  <span class="filename">{{ attachment.originalName }}</span>
                </div>
                <button 
                  @click="downloadAttachment(attachment.originalName)"
                  class="download-btn"
                  :disabled="downloadingFile === attachment.originalName"
                >
                  <i v-if="downloadingFile === attachment.originalName" class="fas fa-spinner fa-spin"></i>
                  <i v-else class="fas fa-download"></i>
                  {{ downloadingFile === attachment.originalName ? 'Downloading...' : 'Download' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Review Form Section -->
      <div class="review-section">
        <div class="section-header">
          <h2>
            <i class="fas fa-edit"></i>
            {{ isCompleted ? 'Your Evaluation' : 'Evaluate the Submission' }}
          </h2>
          <div v-if="isCompleted" class="completed-badge">
            <i class="fas fa-check-circle"></i>
            Completed on {{ formatDate(reviewData?.submittedAt) }}
          </div>
        </div>

        <div class="review-form-card">
          <form @submit.prevent="submitReview">
            <!-- Sezione criteri migliorata -->
            <div class="criteria-section">
              <div class="criteria-header">
                <h3><i class="fas fa-clipboard-check"></i> Evaluation Criteria</h3>
                <div class="progress-indicator">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: overallProgress + '%' }"></div>
                  </div>
                  <span class="progress-text">{{ Math.round(overallProgress) }}% completed</span>
                </div>
              </div>
              <p class="criteria-description">
                <i class="fas fa-lightbulb"></i>
                Evaluate each criterion and provide constructive feedback to help your peer improve.
              </p>

              <div 
                v-for="(criterion, index) in evaluationCriteria" 
                :key="index"
                class="criterion-card"
                :class="{ 'completed': criterion.score > 0 }"
              >
                <div class="criterion-header-enhanced">
                  <div class="criterion-title">
                    <div class="criterion-icon" :class="getScoreClass(criterion.score, getMaxScore(criterion))">
                      <i :class="getScoreIcon(criterion.score, getMaxScore(criterion))"></i>
                    </div>
                    <div>
                      <label :for="`criterion-${index}`" class="criterion-label-enhanced">
                        {{ criterion.criterion }}
                      </label>
                      <div class="score-badge" :class="getScoreClass(criterion.score, getMaxScore(criterion))">
                        {{ getScoreLabel(criterion.score, getMaxScore(criterion)) }}
                      </div>
                    </div>
                  </div>
                  <div class="score-display-enhanced">
                    <span class="score-value-large" :class="getScoreClass(criterion.score, getMaxScore(criterion))">
                      {{ criterion.score }}
                    </span>
                    <span class="score-max">/ {{ getMaxScore(criterion) }}</span>
                  </div>
                </div>

                <div class="score-input-enhanced">
                  <div class="slider-container">
                    <input
                      :id="`criterion-${index}`"
                      v-model.number="criterion.score"
                      type="range"
                      :min="0"
                      :max="getMaxScore(criterion)"
                      :step="1"
                      class="score-slider-enhanced"
                      :disabled="isCompleted"
                      :style="getSliderStyle(criterion.score, getMaxScore(criterion))"
                    />
                    <div class="slider-track" :style="getSliderTrackStyle(criterion.score, getMaxScore(criterion))"></div>
                  </div>
                  <div class="score-labels-enhanced">
                    <span class="label-item"><i class="fas fa-times-circle text-danger"></i> 0</span>
                    <span class="label-item"><i class="fas fa-exclamation-circle text-warning"></i> {{ Math.round(getMaxScore(criterion) * 0.25) }}</span>
                    <span class="label-item"><i class="fas fa-minus-circle text-info"></i> {{ Math.round(getMaxScore(criterion) * 0.5) }}</span>
                    <span class="label-item"><i class="fas fa-check-circle text-success"></i> {{ Math.round(getMaxScore(criterion) * 0.75) }}</span>
                    <span class="label-item"><i class="fas fa-star text-warning"></i> {{ getMaxScore(criterion) }}</span>
                  </div>
                </div>

                <div class="feedback-input-enhanced">
                  <label :for="`feedback-${index}`" class="feedback-label-enhanced">
                    <i class="fas fa-comment-dots"></i>
                    Feedback for "{{ criterion.criterion }}":
                  </label>
                  <div class="textarea-container">
                    <textarea
                      :id="`feedback-${index}`"
                      v-model="criterion.feedback"
                      class="feedback-textarea-enhanced"
                      :placeholder="isCompleted ? 'No feedback provided' : 'Write constructive and specific feedback...'"
                      rows="3"
                      :disabled="isCompleted"
                    ></textarea>
                    <div class="character-counter">
                      {{ criterion.feedback?.length || 0 }} characters
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Submit Button -->
            <div v-if="!isCompleted" class="submit-section">
              <button 
                type="submit" 
                class="submit-btn"
                :disabled="submitting || !isFormValid"
              >
                <i v-if="submitting" class="fas fa-spinner fa-spin"></i>
                <i v-else class="fas fa-paper-plane"></i>
                {{ submitting ? 'Submitting...' : 'Submit Peer Review' }}
              </button>
              <p class="submit-note">
                Once submitted, the peer review can no longer be edited.
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import reviewService from '@/services/reviewService';
import axios from 'axios';

export default {
  name: 'PeerReviewFormPage',
  setup() {
    const route = useRoute();
    const router = useRouter();
    
    const loading = ref(true);
    const error = ref(null);
    const submitting = ref(false);
    const downloadingFile = ref(null);
    
    const reviewData = ref(null);
    const submissionData = ref(null);
    const evaluationCriteria = ref([]);
    const assignmentData = ref(null);

    const reviewId = computed(() => route.params.reviewId);
    const isCompleted = computed(() => !!reviewData.value?.submittedAt);
    const isFormValid = computed(() => {
      return evaluationCriteria.value.every(criterion => {
        const maxScore = assignmentData.value?.rubric?.find(r => r.criterion === criterion.criterion)?.maxScore || 100;
        return criterion.score >= 0 && criterion.score <= maxScore;
      });
    });

    const fetchAssignmentData = async (assignmentId) => {
      try {
        const response = await axios.get(`/assignments/${assignmentId}`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('userToken')}`
          }
        });
        assignmentData.value = response.data;
        
        // Initialize evaluation criteria from assignment rubric
        if (response.data.rubric && response.data.rubric.length > 0) {
          evaluationCriteria.value = response.data.rubric.map(rubricItem => ({
            criterion: rubricItem.criterion,
            score: 0,
            feedback: '',
            maxScore: rubricItem.maxScore
          }));
        }
      } catch (err) {
        console.error('Error fetching assignment data:', err);
        // Fallback to default criteria if assignment fetch fails
        evaluationCriteria.value = [
          { criterion: 'Work Completeness', score: 0, feedback: '', maxScore: 100 },
          { criterion: 'Content Quality', score: 0, feedback: '', maxScore: 100 }
        ];
      }
    };

    const fetchReviewData = async () => {
      try {
        loading.value = true;
        error.value = null;

        // Get review details
        const review = await reviewService.getPeerReviewById(reviewId.value);
        reviewData.value = review;

        // Fetch assignment data to get rubric
        if (review.assignmentId) {
          await fetchAssignmentData(review.assignmentId);
        }

        // If review is completed, populate the evaluation criteria
        if (review.evaluation && review.evaluation.length > 0) {
          evaluationCriteria.value = review.evaluation.map(item => ({ ...item }));
        }

        // Get submission details
        const submission = await reviewService.getSubmissionForReview(review.submissionId);
        submissionData.value = submission;

      } catch (err) {
        console.error('Error fetching review data:', err);
        error.value = err.response?.data?.error || 'Error loading data';
      } finally {
        loading.value = false;
      }
    };

    const downloadAttachment = async (filename) => {
      try {
        downloadingFile.value = filename;
        
        const response = await reviewService.downloadSubmissionAttachment(
          reviewData.value.submissionId, 
          filename
        );
        
        // Check if the response is a valid file
        if (response.headers['content-type'] === 'application/octet-stream') {
          // Create download link
          const url = window.URL.createObjectURL(new Blob([response.data]));
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', filename);
          document.body.appendChild(link);
          link.click();
          link.remove();
          window.URL.revokeObjectURL(url);
        } else {
          // The response may be a JSON error
          const text = await response.data.text();
          const errorData = JSON.parse(text);
          throw new Error(errorData.message || 'Error downloading file');
        }
        
      } catch (err) {
        console.error('Error downloading attachment:', err);
        let errorMessage = 'Error downloading file';
        
        if (err.response) {
          // HTTP error from server
          if (err.response.status === 404) {
            errorMessage = 'File not found';
          } else if (err.response.status === 403) {
            errorMessage = 'You do not have permission to download this file';
          } else if (err.response.data && typeof err.response.data === 'string') {
            try {
              const errorData = JSON.parse(err.response.data);
              errorMessage = errorData.message || errorMessage;
            } catch {
              errorMessage = err.response.data;
            }
          }
        } else {
          errorMessage = err.message;
        }
        
        alert(errorMessage);
      } finally {
        downloadingFile.value = null;
      }
    };

    const submitReview = async () => {
      try {
        submitting.value = true;
        
        // Remove maxScore field before sending data
        const evaluationData = evaluationCriteria.value.map(criterion => ({
          criterion: criterion.criterion,
          score: criterion.score,
          feedback: criterion.feedback || null
        }));
        
        await reviewService.submitPeerReview(reviewId.value, evaluationData);
        
        alert('Peer review submitted successfully!');
        router.push({ name: 'StudentPeerReviews' });
        
      } catch (err) {
        console.error('Error submitting review:', err);
        alert('Error submitting the peer review: ' + (err.response?.data?.error || err.message));
      } finally {
        submitting.value = false;
      }
    };

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A';
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    };

    onMounted(() => {
      fetchReviewData();
    });

    const getMaxScore = (criterion) => {
      return criterion.maxScore || assignmentData.value?.rubric?.find(r => r.criterion === criterion.criterion)?.maxScore || 100;
    };

    const overallProgress = computed(() => {
      if (!evaluationCriteria.value.length) return 0;
      const totalCriteria = evaluationCriteria.value.length;
      const completedCriteria = evaluationCriteria.value.filter(c => c.score > 0).length;
      return (completedCriteria / totalCriteria) * 100;
    });

    const getScoreClass = (score, maxScore) => {
      const percentage = (score / maxScore) * 100;
      if (percentage === 0) return '';
      if (percentage <= 25) return 'score-low';
      if (percentage <= 50) return 'score-medium';
      if (percentage <= 75) return 'score-high';
      return 'score-excellent';
    };

    const getScoreIcon = (score, maxScore) => {
      const percentage = (score / maxScore) * 100;
      if (percentage === 0) return 'fas fa-circle';
      if (percentage <= 25) return 'fas fa-frown';
      if (percentage <= 50) return 'fas fa-meh';
      if (percentage <= 75) return 'fas fa-smile';
      return 'fas fa-star';
    };

    const getScoreLabel = (score, maxScore) => {
      const percentage = (score / maxScore) * 100;
      if (percentage === 0) return 'Not evaluated';
      if (percentage <= 25) return 'Insufficient';
      if (percentage <= 50) return 'Sufficient';
      if (percentage <= 75) return 'Good';
      return 'Excellent';
    };

    const getSliderStyle = (score, maxScore) => {
      const percentage = (score / maxScore) * 100;
      return {
        background: `linear-gradient(90deg, 
          #e74c3c 0%, 
          #f39c12 ${Math.min(percentage, 25)}%, 
          #3498db ${Math.min(percentage, 50)}%, 
          #27ae60 ${Math.min(percentage, 75)}%, 
          #27ae60 100%)`
      };
    };

    const getSliderTrackStyle = (score, maxScore) => {
      const percentage = (score / maxScore) * 100;
      return {
        background: `linear-gradient(90deg, 
          #e2e8f0 0%, 
          #e2e8f0 ${percentage}%, 
          #cbd5e0 ${percentage}%, 
          #cbd5e0 100%)`
      };
    };

    return {
      loading,
      error,
      submitting,
      downloadingFile,
      reviewData,
      submissionData,
      evaluationCriteria,
      assignmentData,
      reviewId,
      isCompleted,
      isFormValid,
      fetchReviewData,
      downloadAttachment,
      submitReview,
      formatDate,
      getMaxScore,
      overallProgress,
      getScoreClass,
      getScoreIcon,
      getScoreLabel,
      getSliderStyle,
      getSliderTrackStyle
    };
  }
};
</script>

<style scoped>
.peer-review-form-page {
  max-width: 1000px;
  margin: 20px auto;
  padding: 20px;
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

.loading i {
  font-size: 24px;
  margin-right: 10px;
}

.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.back-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  margin-bottom: 20px;
  transition: background 0.3s ease;
}

.back-btn:hover {
  background: #5a6268;
}

.header-section {
  margin-bottom: 30px;
}

.header-section h1 {
  color: #333;
  margin: 10px 0;
}

.header-section h1 i {
  color: #9B59B6;
  margin-right: 10px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  color: #333;
  margin: 0;
}

.section-header h2 i {
  margin-right: 10px;
  color: #007bff;
}

.completed-badge {
  background: #d4edda;
  color: #155724;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
  border: 1px solid #c3e6cb;
}

.completed-badge i {
  margin-right: 5px;
}

.submission-section, .review-section {
  margin-bottom: 30px;
}

.submission-card, .review-form-card {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
}

.submission-info {
  margin-bottom: 20px;
}

.info-row {
  display: flex;
  margin-bottom: 10px;
}

.label {
  font-weight: 600;
  color: #495057;
  min-width: 120px;
}

.value {
  color: #333;
}

.submission-text {
  margin-bottom: 20px;
}

.submission-text h4 {
  color: #333;
  margin-bottom: 10px;
}

.text-content {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  border-left: 4px solid #007bff;
  white-space: pre-wrap;
  line-height: 1.6;
}

.attachments-section h4 {
  color: #333;
  margin-bottom: 15px;
}

.attachments-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.attachment-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.attachment-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.attachment-info i {
  color: #6c757d;
}

.filename {
  font-weight: 500;
}

.download-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s ease;
}

.download-btn:hover:not(:disabled) {
  background: #218838;
}

.download-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.criteria-section h3 {
  color: #333;
  margin-bottom: 10px;
}

.criteria-description {
  color: #6c757d;
  margin-bottom: 25px;
  font-style: italic;
}

.criterion-item {
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.criterion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.criterion-label {
  font-weight: 600;
  color: #333;
  font-size: 16px;
}

.score-display {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.score-value {
  font-size: 24px;
  font-weight: 700;
  color: #007bff;
}

.score-max {
  font-size: 16px;
  color: #6c757d;
}

.score-input {
  margin-bottom: 15px;
}

.score-slider {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: #e9ecef;
  outline: none;
  margin-bottom: 10px;
}

.score-slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
}

.score-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: none;
}

.score-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #6c757d;
}

.feedback-label {
  display: block;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.feedback-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  min-height: 80px;
}

.feedback-textarea:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.feedback-textarea:disabled {
  background: #e9ecef;
  color: #6c757d;
}

.submit-section {
  text-align: center;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
}

.submit-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 15px 30px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s ease;
  margin-bottom: 10px;
}

.submit-btn:hover:not(:disabled) {
  background: #218838;
}

.submit-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.submit-note {
  color: #6c757d;
  font-size: 14px;
  font-style: italic;
  margin: 0;
}

/* Design formale e moderno */
.criteria-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 25px;
  background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  border-radius: 12px;
  color: white;
  box-shadow: 0 4px 20px rgba(44, 62, 80, 0.15);
}

.criteria-header h3 {
  margin: 0;
  color: white;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.progress-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  width: 140px;
  height: 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3498db, #2980b9);
  transition: width 0.4s ease;
  border-radius: 3px;
}

.progress-text {
  font-size: 13px;
  font-weight: 500;
  opacity: 0.9;
}

.criteria-description {
  background: linear-gradient(135deg, #ecf0f1 0%, #bdc3c7 100%);
  color: #2c3e50;
  padding: 18px 24px;
  border-radius: 10px;
  margin-bottom: 25px;
  font-style: normal;
  border-left: 4px solid #3498db;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.criteria-description i {
  margin-right: 8px;
  color: #3498db;
}

.criterion-card {
  margin-bottom: 24px;
  padding: 28px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e8eaed;
  transition: all 0.3s ease;
  position: relative;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.criterion-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3498db, #2980b9);
  transform: scaleX(0);
  transition: transform 0.3s ease;
  border-radius: 12px 12px 0 0;
}

.criterion-card:hover::before,
.criterion-card.completed::before {
  transform: scaleX(1);
}

.criterion-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
  border-color: #3498db;
}

.criterion-header-enhanced {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.criterion-title {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.criterion-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.3s ease;
  background: #f8f9fa;
  border: 2px solid #e9ecef;
}

.criterion-icon.score-low {
  background: #fff5f5;
  border-color: #fed7d7;
  color: #e53e3e;
}

.criterion-icon.score-medium {
  background: #fffaf0;
  border-color: #fbd38d;
  color: #dd6b20;
}

.criterion-icon.score-high {
  background: #ebf8ff;
  border-color: #90cdf4;
  color: #3182ce;
}

.criterion-icon.score-excellent {
  background: #f0fff4;
  border-color: #9ae6b4;
  color: #38a169;
}

.criterion-label-enhanced {
  font-weight: 600;
  color: #2d3748;
  font-size: 17px;
  margin-bottom: 6px;
  display: block;
  line-height: 1.3;
}

.score-badge {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  border: 1px solid;
}

.score-badge.score-low {
  background: #fff5f5;
  color: #c53030;
  border-color: #fed7d7;
}

.score-badge.score-medium {
  background: #fffaf0;
  color: #d69e2e;
  border-color: #fbd38d;
}

.score-badge.score-high {
  background: #ebf8ff;
  color: #3182ce;
  border-color: #90cdf4;
}

.score-badge.score-excellent {
  background: #f0fff4;
  color: #38a169;
  border-color: #9ae6b4;
}

.score-display-enhanced {
  text-align: right;
}

.score-value-large {
  font-size: 32px;
  font-weight: 700;
  transition: color 0.3s ease;
  font-family: 'Segoe UI', system-ui, sans-serif;
}

.score-value-large.score-low {
  color: #e53e3e;
}

.score-value-large.score-medium {
  color: #dd6b20;
}

.score-value-large.score-high {
  color: #3182ce;
}

.score-value-large.score-excellent {
  color: #38a169;
}

.score-input-enhanced {
  margin-bottom: 24px;
}

.slider-container {
  position: relative;
  margin-bottom: 16px;
}

.score-slider-enhanced {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: transparent;
  outline: none;
  position: relative;
  z-index: 2;
}

.score-slider-enhanced::-webkit-slider-thumb {
  appearance: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(52, 152, 219, 0.2);
  border: 2px solid #3498db;
  transition: all 0.2s ease;
}

.score-slider-enhanced::-webkit-slider-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2), 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.slider-track {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 8px;
  border-radius: 4px;
  transform: translateY(-50%);
  z-index: 1;
  background: #e2e8f0;
}

.score-labels-enhanced {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
}

.label-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 11px;
  color: #718096;
  font-weight: 500;
}

.label-item i {
  font-size: 14px;
  margin-bottom: 4px;
  opacity: 0.7;
}

.feedback-input-enhanced {
  margin-top: 24px;
}

.feedback-label-enhanced {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 12px;
  font-size: 15px;
}

.feedback-label-enhanced i {
  margin-right: 8px;
  color: #4a5568;
}

.textarea-container {
  position: relative;
}

.feedback-textarea-enhanced {
  width: 100%;
  padding: 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  min-height: 90px;
  transition: all 0.2s ease;
  background: #fafafa;
}

.feedback-textarea-enhanced:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
  background: white;
}

.character-counter {
  position: absolute;
  bottom: 10px;
  right: 14px;
  font-size: 11px;
  color: #a0aec0;
  background: rgba(255, 255, 255, 0.9);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

/* Utility classes con colori più formali */
.text-danger { color: #e53e3e !important; }
.text-warning { color: #dd6b20 !important; }
.text-info { color: #3182ce !important; }
.text-success { color: #38a169 !important; }

/* Animazioni più sottili */
@keyframes subtlePulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.02); }
  100% { transform: scale(1); }
}

.criterion-card.completed .criterion-icon {
  animation: subtlePulse 3s infinite;
}

/* Miglioramenti per il submit button */
.submit-btn {
  background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  color: white;
  border: none;
  padding: 16px 32px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 12px;
  letter-spacing: 0.3px;
  box-shadow: 0 4px 12px rgba(44, 62, 80, 0.15);
}

.submit-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(44, 62, 80, 0.2);
}

.submit-btn:disabled {
  background: #95a5a6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
</style>
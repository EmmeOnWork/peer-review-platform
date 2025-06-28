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
                    <span class="required-indicator">*</span>
                  </label>
                  <div class="textarea-container">
                    <textarea
                      :id="`feedback-${index}`"
                      v-model="criterion.feedback"
                      class="feedback-textarea-enhanced"
                      :class="{ 
                        'error': !isCompleted && criterion.score > 0 && (!criterion.feedback || criterion.feedback.trim().length === 0),
                        'warning': !isCompleted && criterion.score === 0
                      }"
                      :placeholder="isCompleted ? 'No feedback provided' : 'Write constructive and specific feedback... (Required)'"
                      rows="3"
                      :disabled="isCompleted"
                      required
                    ></textarea>
                    <div class="character-counter">
                      {{ criterion.feedback?.length || 0 }} characters
                      <span v-if="!isCompleted && (!criterion.feedback || criterion.feedback.trim().length === 0)" class="required-text">
                        (Required)
                      </span>
                    </div>
                  </div>
                  
                  <!-- Messaggio di errore -->
                  <div v-if="!isCompleted && criterion.score > 0 && (!criterion.feedback || criterion.feedback.trim().length === 0)" 
                       class="validation-error">
                  <i class="fas fa-exclamation-circle"></i>
                  Feedback is required when assigning a score
                  </div>
                  
                  <!-- Avviso per score 0 -->
                  <div v-if="!isCompleted && criterion.score === 0" 
                       class="validation-warning">
                  <i class="fas fa-info-circle"></i>
                  Please assign a score and provide feedback
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
                <span v-if="!isFormValid" class="validation-message">
                  <i class="fas fa-exclamation-triangle"></i>
                  Please assign scores greater than 0 and provide feedback for all criteria before submitting.
                </span>
                <span v-else>
                  Once submitted, the peer review can no longer be edited.
                </span>
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
        return (
          // Score deve essere maggiore di 0 (non solo >= 0)
          criterion.score > 0 && 
          criterion.score <= maxScore &&
          // Feedback deve essere presente e non vuoto
          criterion.feedback && 
          criterion.feedback.trim().length > 0
        );
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
  background: #95a5a6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
  opacity: 0.6;
}

/* Indicatore campo obbligatorio */
.required-indicator {
  color: #e53e3e;
  font-weight: bold;
  margin-left: 4px;
}

/* Stili per i campi con errore */
.feedback-textarea-enhanced.error {
  border-color: #e53e3e;
  background: #fff5f5;
}

.feedback-textarea-enhanced.error:focus {
  border-color: #e53e3e;
  box-shadow: 0 0 0 3px rgba(229, 62, 62, 0.1);
}

.feedback-textarea-enhanced.warning {
  border-color: #dd6b20;
  background: #fffaf0;
}

/* Messaggi di validazione */
.validation-error {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 8px 12px;
  background: #fff5f5;
  border: 1px solid #fed7d7;
  border-radius: 6px;
  color: #c53030;
  font-size: 13px;
  font-weight: 500;
}

.validation-warning {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 8px 12px;
  background: #fffaf0;
  border: 1px solid #fbd38d;
  border-radius: 6px;
  color: #d69e2e;
  font-size: 13px;
  font-weight: 500;
}

.validation-message {
  color: #d69e2e;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.required-text {
  color: #e53e3e;
  font-weight: 600;
}

/* Miglioramento del button submit */
.submit-btn:disabled {
  background: #95a5a6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
  opacity: 0.6;
}
</style>
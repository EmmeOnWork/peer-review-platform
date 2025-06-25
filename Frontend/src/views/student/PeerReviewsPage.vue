<template>
  <div class="peer-reviews-page">
    <div class="header-section">
      <h1><i class="fas fa-star"></i> Peer Reviews</h1>
      <p>Rivedi il lavoro dei tuoi compagni di classe</p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <i class="fas fa-spinner fa-spin"></i>
      <span>Caricamento peer reviews...</span>
    </div>

    <!-- Error -->
    <div v-if="error" class="error">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && !error && reviews.length === 0" class="empty">
      <i class="fas fa-clipboard-list"></i>
      <h3>Nessuna Peer Review Assegnata</h3>
      <p>Al momento non hai peer review da completare.</p>
    </div>

    <!-- Reviews List -->
    <div v-if="!loading && !error && reviews.length > 0" class="reviews-container">
      <div class="reviews-grid">
        <div 
          v-for="review in reviews" 
          :key="review.reviewId" 
          class="review-card"
          :class="{ 'completed': review.submittedAt }"
        >
          <div class="review-header">
            <div class="review-status">
              <i v-if="review.submittedAt" class="fas fa-check-circle completed-icon"></i>
              <i v-else class="fas fa-clock pending-icon"></i>
              <span class="status-text">
                {{ review.submittedAt ? 'Completata' : 'In Attesa' }}
              </span>
            </div>
            <div class="review-date">
              <small>Assegnata: {{ formatDate(review.createdAt) }}</small>
            </div>
          </div>

          <div class="review-content">
            <div class="author-info">
              <p class="assignment-id">Assignment: {{ review.assignmentId }}</p>
            </div>

            <div class="review-actions">
              <button 
                @click="startReview(review.reviewId)" 
                class="review-btn"
                :class="{ 'completed': review.submittedAt }"
              >
                <i :class="review.submittedAt ? 'fas fa-eye' : 'fas fa-edit'"></i>
                {{ review.submittedAt ? 'Visualizza Review' : 'Inizia Review' }}
              </button>
            </div>
          </div>

          <div v-if="review.submittedAt" class="completion-info">
            <small>Completata il: {{ formatDate(review.submittedAt) }}</small>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import reviewService from '@/services/reviewService';

export default {
  name: 'PeerReviewsPage',
  setup() {
    const router = useRouter();
    const store = useStore();
    const reviews = ref([]);
    const loading = ref(true);
    const error = ref(null);

    const user = computed(() => store.state.user);

    const fetchPeerReviews = async () => {
      try {
        loading.value = true;
        error.value = null;
        
        const studentSerialNumber = user.value?.serialNumber;
        if (!studentSerialNumber) {
          throw new Error('Serial number dello studente non trovato');
        }

        const data = await reviewService.getStudentPeerReviews(studentSerialNumber);
        reviews.value = data;
      } catch (err) {
        console.error('Error fetching peer reviews:', err);
        error.value = err.response?.data?.error || 'Errore nel caricamento delle peer reviews';
      } finally {
        loading.value = false;
      }
    };

    const startReview = (reviewId) => {
      router.push({ name: 'PeerReviewForm', params: { reviewId } });
    };

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A';
      return new Date(dateString).toLocaleDateString('it-IT', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    };

    onMounted(() => {
      fetchPeerReviews();
    });

    return {
      reviews,
      loading,
      error,
      startReview,
      formatDate
    };
  }
};
</script>

<style scoped>
.peer-reviews-page {
  max-width: 1200px;
  margin: 20px auto;
  padding: 20px;
}

.header-section {
  text-align: center;
  margin-bottom: 30px;
}

.header-section h1 {
  color: #333;
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

.loading i {
  font-size: 24px;
  margin-right: 10px;
}

.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.empty {
  background: #e2e3e5;
  color: #383d41;
}

.empty i {
  font-size: 48px;
  margin-bottom: 15px;
  color: #6c757d;
}

.reviews-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.review-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 2px solid #e9ecef;
  transition: all 0.3s ease;
}

.review-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.review-card.completed {
  border-color: #28a745;
  background: linear-gradient(135deg, #ffffff 0%, #f8fff9 100%);
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.review-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.completed-icon {
  color: #28a745;
}

.pending-icon {
  color: #ffc107;
}

.status-text {
  font-weight: 600;
  font-size: 14px;
}

.review-date small {
  color: #6c757d;
  font-size: 12px;
}

.author-info h3 {
  margin: 0 0 5px 0;
  color: #333;
  font-size: 18px;
}

.assignment-id {
  color: #6c757d;
  font-size: 14px;
  margin: 0 0 15px 0;
}

.review-btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 8px;
  background: #9B59B6;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s ease;
}

.review-btn:hover {
  background: #8e44ad;
}

.review-btn.completed {
  background: #28a745;
}

.review-btn.completed:hover {
  background: #218838;
}

.completion-info {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e9ecef;
  text-align: center;
}

.completion-info small {
  color: #28a745;
  font-weight: 500;
}
</style>
<template>
  <div class="submission-page">
    <div class="header">
      <button @click="goBack" class="back-btn">
        <i class="fas fa-arrow-left"></i>
      </button>
      <div class="header-content">
        <h1><i class="fas fa-paper-plane"></i> Invia Submission</h1>
        <p>Completa e invia la tua submission per l'assignment</p>
      </div>
    </div>
    <SubmissionForm />
  </div>
</template>

<script>
import SubmissionForm from '@/components/submission/SubmissionForm.vue';
import { useRouter } from 'vue-router';

export default {
  name: 'SubmissionFormPage',
  components: {
    SubmissionForm
  },
  setup() {
    const router = useRouter();
    
    const goBack = () => {
      router.go(-1);
    };
    
    return {
      goBack
    };
  }
};
</script>

<style scoped>
.submission-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  background: #f8f9fa;
  min-height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  gap: 20px;
  background: white;
  padding: 25px 30px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  margin-bottom: 25px;
}

.back-btn {
  width: 45px;
  height: 45px;
  background: #6c5ce7;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.back-btn:hover {
  background: #5a4fcf;
  transform: translateY(-1px);
}

.header-content {
  flex: 1;
}

.header-content h1 {
  color: #2d3436;
  font-size: 1.8rem;
  font-weight: 600;
  margin: 0 0 5px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-content h1 i {
  color: #6c5ce7;
}

.header-content p {
  color: #636e72;
  font-size: 1rem;
  margin: 0;
}

@media (max-width: 768px) {
  .submission-page {
    padding: 10px;
  }
  
  .header {
    padding: 20px;
    flex-direction: column;
    text-align: center;
  }
  
  .back-btn {
    align-self: flex-start;
  }
}
</style>
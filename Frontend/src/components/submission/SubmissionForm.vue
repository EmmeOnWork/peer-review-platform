<template>
  <div class="submission-form">
    <!-- Loading -->
    <div v-if="loading" class="loading">
      <i class="fas fa-spinner fa-spin"></i>
      <span>Loading...</span>
    </div>

    <!-- Error -->
    <div v-if="error" class="error">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
    </div>

    <!-- Success -->
    <div v-if="success" class="success">
      <i class="fas fa-check-circle"></i>
      <h3>Submission Sent!</h3>
      <p>{{ success }}</p>

    </div>
    
    <!-- Form -->
    <form @submit.prevent="submitForm" v-if="!loading && !success" class="form">
      <!-- Text Area -->
      <div class="form-card">
        <div class="card-header">
          <h3><i class="fas fa-edit"></i>Submission Text</h3>
        </div>
        <div class="card-content">
          <textarea 
            v-model="formData.text" 
            rows="6" 
            placeholder="Enter your submission text here..."
            class="text-input"
          ></textarea>
        </div>
      </div>

      <!-- File Upload -->
      <div class="form-card">
        <div class="card-header">
          <h3><i class="fas fa-paperclip"></i> Attachments</h3>
          <span class="file-limit">Max 5 file (PDF, ZIP, TXT, DOCX)</span>
        </div>
        <div class="card-content">
          <div class="file-upload">
            <input 
              type="file" 
              id="attachments" 
              @change="handleFileChange" 
              multiple
              accept=".pdf,.zip,.txt,.docx"
              class="file-input"
            >
            <label for="attachments" class="file-label">
              <i class="fas fa-cloud-upload-alt"></i>
              <span>Choose file or drag here</span>
              <small>Maximum size: 10MB per file</small>
            </label>
          </div>

          <!-- Selected Files -->
          <div v-if="selectedFiles.length > 0" class="selected-files">
            <h4>File selezionati:</h4>
            <div class="files-list">
              <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
                <i class="fas fa-file"></i>
                <div class="file-info">
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">{{ formatFileSize(file.size) }}</span>
                </div>
                <button type="button" @click="removeFile(index)" class="remove-btn">
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Actions -->
      <div class="form-actions">
        <button type="button" @click="goBack" class="cancel-btn">
          <i class="fas fa-times"></i>
          Cancel
        </button>
        <button type="submit" class="submit-btn" :disabled="isSubmitting">
          <i class="fas" :class="isSubmitting ? 'fa-spinner fa-spin' : 'fa-paper-plane'"></i>
          {{ isSubmitting ? 'Send...' : 'Send Submission' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';

export default {
  name: 'SubmissionForm',
  setup() {
    const route = useRoute();
    const assignmentId = ref(route.params.assignmentId);
    const loading = ref(true);
    const error = ref(null);
    const success = ref(null);
    const isSubmitting = ref(false);
    const selectedFiles = ref([]);
    
    const formData = reactive({
      text: '',
    });
    
    const getAuthHeaders = () => {
      const token = localStorage.getItem('userToken');
      return token ? { Authorization: `Bearer ${token}` } : {};
    };
    
    const fetchAssignmentDetails = async () => {
      try {
        await axios.get(`/assignments/${assignmentId.value}`, {
          headers: getAuthHeaders()
        });
        loading.value = false;
      } catch (err) {
        console.error('Error fetching assignment details:', err);
        error.value = 'Impossibile caricare i dettagli dell\'assignment.';
        loading.value = false;
      }
    };
    
    const handleFileChange = (event) => {
      const files = Array.from(event.target.files);
      
      const validFiles = files.filter(file => {
        const isValidType = [
          'application/pdf',
          'application/zip',
          'text/plain',
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ].includes(file.type);
        
        const isValidSize = file.size <= 10 * 1024 * 1024; // 10MB
        
        if (!isValidType) {
          alert(`File ${file.name} is not a supported type.`);
          return false;
        }
        
        if (!isValidSize) {
          alert(`File ${file.name} is too large (max 10MB).`);
          return false;
        }
        
        return true;
      });
      
      if (selectedFiles.value.length + validFiles.length > 5) {
        alert('Puoi selezionare massimo 5 file.');
        return;
      }
      
      selectedFiles.value = [...selectedFiles.value, ...validFiles];
      event.target.value = '';
    };
    
    const removeFile = (index) => {
      selectedFiles.value.splice(index, 1);
    };
    
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };
    
    const submitForm = async () => {
      if (!formData.text.trim() && selectedFiles.value.length === 0) {
        alert('Inserisci almeno un testo o un allegato.');
        return;
      }
      
      isSubmitting.value = true;
      error.value = null;
      
      try {
        const formDataToSend = new FormData();
        formDataToSend.append('assignmentId', assignmentId.value);
        formDataToSend.append('text', formData.text);
        
        selectedFiles.value.forEach((file) => {
          formDataToSend.append('attachments', file);
        });
        
        await axios.post('/submissions', formDataToSend, {
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'multipart/form-data'
          }
        });
        
        success.value = 'Your submission has been successfully submitted!';
      } catch (err) {
        console.error('Error submitting:', err);
        if (err.response?.status === 400) {
          error.value = err.response.data.message || 'Invalid data.';
        } else if (err.response?.status === 401) {
          error.value = 'Unauthorized. Please log in again.';
        } else {
          error.value = 'Error during submission. Please try again later.';
        }
      } finally {
        isSubmitting.value = false;
      }
    };
    
    onMounted(fetchAssignmentDetails);
    
    return {
      formData, selectedFiles, loading, error, success, isSubmitting,
      handleFileChange, removeFile, formatFileSize, submitForm
    };
  }
};
</script>

<style scoped>
.submission-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.loading, .error, .success {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
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
  font-size: 2.5rem;
  color: #e74c3c;
}

.success {
  gap: 15px;
}

.success i {
  font-size: 3rem;
  color: #00b894;
}

.success h3 {
  color: #2d3436;
  margin: 0;
}

.success p {
  color: #636e72;
  margin: 0;
}

.success-btn {
  background: #00b894;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.success-btn:hover {
  background: #00a085;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  overflow: hidden;
}

.card-header {
  background: #f8f9fa;
  padding: 20px 25px;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  color: #2d3436;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-header h3 i {
  color: #6c5ce7;
}

.file-limit {
  color: #636e72;
  font-size: 0.85rem;
  background: #e9ecef;
  padding: 4px 8px;
  border-radius: 4px;
}

.card-content {
  padding: 25px;
}

.text-input {
  width: 100%;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  padding: 15px;
  font-size: 1rem;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.3s ease;
}

.text-input:focus {
  outline: none;
  border-color: #6c5ce7;
}

.file-upload {
  position: relative;
  margin-bottom: 20px;
}

.file-input {
  position: absolute;
  opacity: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
}

.file-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px 20px;
  border: 2px dashed #ddd;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.file-label:hover {
  border-color: #6c5ce7;
  background: #f8f9fa;
}

.file-label i {
  font-size: 2rem;
  color: #6c5ce7;
}

.file-label span {
  color: #2d3436;
  font-weight: 600;
}

.file-label small {
  color: #636e72;
  font-size: 0.85rem;
}

.selected-files h4 {
  color: #2d3436;
  margin: 0 0 15px 0;
  font-size: 1rem;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.file-item i {
  color: #6c5ce7;
  font-size: 1.2rem;
}

.file-info {
  flex: 1;
}

.file-name {
  display: block;
  color: #2d3436;
  font-weight: 500;
  margin-bottom: 2px;
}

.file-size {
  display: block;
  color: #636e72;
  font-size: 0.85rem;
}

.remove-btn {
  background: #e74c3c;
  color: white;
  border: none;
  width: 30px;
  height: 30px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.remove-btn:hover {
  background: #c0392b;
}

.form-actions {
  display: flex;
  gap: 15px;
  justify-content: flex-end;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.cancel-btn, .submit-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.cancel-btn {
  background: #6c757d;
  color: white;
}

.cancel-btn:hover {
  background: #5a6268;
}

.submit-btn {
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  color: white;
}

.submit-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #5a4fcf, #8b7ff0);
  transform: translateY(-1px);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .cancel-btn, .submit-btn {
    justify-content: center;
  }
}
</style>


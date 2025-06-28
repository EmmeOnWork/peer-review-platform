<template>
  <div class="assignment-form-page">
    <div class="assignment-form-container">
      <div class="form-header">
        <h2>{{ isEditMode ? 'Edit Assignment' : 'Create New Assignment' }}</h2>
        <p class="form-subtitle">{{ isEditMode ? 'Update assignment details and settings' : 'Fill in the details to create a new assignment' }}</p>
      </div>
      
      <form @submit.prevent="handleSubmit" class="assignment-form">
        <!-- Basic Information Section -->
        <div class="form-section">
          <h3 class="section-title">Basic Information</h3>
          
          <div class="form-group">
            <label for="title">Assignment Title</label>
            <input type="text" id="title" v-model="form.title" required placeholder="Enter assignment title" />
          </div>

          <div class="form-group">
            <label for="description">Description</label>
            <textarea id="description" v-model="form.description" rows="4" required placeholder="Describe the assignment objectives and requirements"></textarea>
          </div>

          <div class="form-group">
            <label for="deadline">Deadline</label>
            <input type="datetime-local" id="deadline" v-model="form.deadline" required />
          </div>
        </div>

        <!-- Rubric Section -->
        <div class="form-section">
          <h3 class="section-title">Evaluation Rubric</h3>
          <p class="section-description">Define the criteria and scoring for this assignment</p>
          
          <div class="rubric-container">
            <div v-for="(criterion, index) in form.rubric" :key="index" class="rubric-item">
              <div class="rubric-inputs">
                <input type="text" v-model="criterion.criterion" placeholder="Evaluation criterion" required class="criterion-input" />
                <input type="number" v-model.number="criterion.maxScore" placeholder="Max Score" required min="0" max="100" class="score-input" />
              </div>
              <button type="button" @click="removeCriterion(index)" class="remove-btn" :disabled="form.rubric.length === 1">
                <i class="fas fa-trash"></i>
              </button>
            </div>
            <button type="button" @click="addCriterion" class="add-criterion-btn">
              <i class="fas fa-plus"></i> Add Criterion
            </button>
          </div>
        </div>

        <!-- Student Assignment Section -->
        <div class="form-section">
          <h3 class="section-title">Assign to Students</h3>
          <p class="section-description">Search and select students for this assignment</p>
          
          <div class="student-search-container">
            <div class="search-input-wrapper">
              <i class="fas fa-search search-icon"></i>
              <input type="text" v-model="studentSearchTerm" placeholder="Search students by name or surname..." @input="debouncedSearchStudents" class="student-search-input"/>
            </div>
            
            <div v-if="isLoadingStudents" class="loading-students">
              <i class="fas fa-spinner fa-spin"></i> Loading students...
            </div>
            
            <div v-if="!isLoadingStudents && availableStudents.length === 0 && studentSearchTerm && !errorMessageDisplay" class="info-message">
              <i class="fas fa-info-circle"></i> No students found matching your search.
            </div>
            
            <div v-if="!isLoadingStudents && availableStudents.length === 0 && !studentSearchTerm && !errorMessageDisplay && initialLoadDone" class="info-message">
              <i class="fas fa-users"></i> No students available.
            </div>
            
            <div v-if="availableStudents.length > 0" class="students-list">
              <div v-for="student in availableStudents" :key="student.id" class="student-item">
                <input type="checkbox" :id="'student-' + student.id" :value="student.id" v-model="selectedStudentSerials" class="student-checkbox" />
                <label :for="'student-' + student.id" class="student-label">
                  <div class="student-avatar">
                    <i class="fas fa-user"></i>
                  </div>
                  <span class="student-name">{{ student.name }}</span>
                </label>
              </div>
            </div>
            
            <div v-if="selectedStudentSerials.length > 0" class="selected-count">
              <i class="fas fa-check-circle"></i> {{ selectedStudentSerials.length }} student(s) selected
            </div>
            
            <div v-if="errorMessageDisplay" class="error-message">
              <i class="fas fa-exclamation-triangle"></i> {{ errorMessageDisplay }}
            </div>
          </div>
        </div>

        <!-- Messages -->
        <div v-if="errorMessage" class="message error-message">
          <i class="fas fa-exclamation-circle"></i> {{ errorMessage }}
        </div>
        <div v-if="successMessage" class="message success-message">
          <i class="fas fa-check-circle"></i> {{ successMessage }}
        </div>

        <!-- Form Actions -->
        <div class="form-actions">
          <button type="submit" class="submit-btn">
            <i class="fas fa-save"></i> {{ isEditMode ? 'Update Assignment' : 'Create Assignment' }}
          </button>
          <button type="button" @click="$emit('cancel')" class="cancel-btn">
            <i class="fas fa-times"></i> Cancel
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits, onMounted } from 'vue';
import axios from 'axios';

const props = defineProps({
  assignment: { // Prop to pass existing assignment data for editing
    type: Object,
    default: null
  }
});

const emit = defineEmits(['submitted', 'cancel']);

const form = ref({
  title: '',
  description: '',
  deadline: '',
  rubric: [{ criterion: '', maxScore: 0 }],
  students: [] // This will now store selected student objects or IDs
});

// const studentsInput = ref(''); // REMOVED: Unused variable
const availableStudents = ref([]);
const selectedStudentSerials = ref([]);
const errorMessage = ref('');
const successMessage = ref('');
const isEditMode = ref(false);
const initialLoadDone = ref(false); // New ref to track initial student load

// AGGIUNTA: Definizione della funzione resetForm
function resetForm() {
  form.value.title = '';
  form.value.description = '';
  form.value.deadline = '';
  form.value.rubric = [{ criterion: '', maxScore: 0 }];
  form.value.students = [];
  selectedStudentSerials.value = [];
  // studentSearchTerm.value = ''; // Già gestito altrove o può essere aggiunto se necessario qui
  errorMessage.value = '';
  successMessage.value = '';
  // isEditMode.value = false; // Questo è già gestito nel watcher di props.assignment
}

const API_URL = '/assignments';
const AUTH_API_URL = '/auth'; // Define Auth API URL

const getAuthHeaders = () => {
  const token = localStorage.getItem('userToken');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const studentSearchTerm = ref('');
const isLoadingStudents = ref(false);
let debounceTimer = null;
const errorMessageDisplay = ref(''); // Renamed from errorMessage to avoid conflict with form-wide errorMessage

// Fetch available students when the component is mounted
onMounted(async () => {
  await fetchAvailableStudents(); // Initial load of all students
  initialLoadDone.value = true;
});

async function fetchAvailableStudents(searchTerm = '') {
  isLoadingStudents.value = true;
  errorMessageDisplay.value = '';
  let url = `${AUTH_API_URL}/users/students`; // Default to all students
  const params = {};

  if (searchTerm) {
    url = `${AUTH_API_URL}/users/search`;
    // Assuming the backend can handle a single search term for name/surname
    // Or, you might need to split searchTerm into name and surname if your API requires it
    params.name = searchTerm; // Or params.query = searchTerm, depending on API
    // params.surname = searchTerm; // if you want to search in both with the same term
  }

  try {
    const response = await axios.get(url, { headers: getAuthHeaders(), params });
    availableStudents.value = response.data.map(student => ({
      id: student.serialNumber, // Ensure this matches the field from your API
      name: `${student.name} ${student.surname} (${student.serialNumber})`
    }));
    if (availableStudents.value.length === 0 && !searchTerm && initialLoadDone.value) {
        // This message is now handled in the template based on conditions
    } else if (availableStudents.value.length === 0 && searchTerm) {
        // This message is now handled in the template
    }
  } catch (err) {
    console.error('Error fetching students:', err.response || err.message);
    errorMessageDisplay.value = 'Failed to load student list. Please try again.';
    availableStudents.value = []; // Clear on error
  } finally {
    isLoadingStudents.value = false;
  }
}

const debouncedSearchStudents = () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    fetchAvailableStudents(studentSearchTerm.value.trim());
  }, 500); // 500ms debounce
};

watch(studentSearchTerm, (newValue) => {
  if (newValue.trim() === '') {
    // If search term is cleared, fetch all students again
    fetchAvailableStudents();
  }
});

watch(() => props.assignment, (newVal) => {
  if (newVal) {
    isEditMode.value = true;
    form.value.title = newVal.title;
    form.value.description = newVal.description;
    form.value.deadline = newVal.deadline ? new Date(newVal.deadline).toISOString().slice(0, 16) : '';
    form.value.rubric = newVal.rubric && newVal.rubric.length > 0 ? JSON.parse(JSON.stringify(newVal.rubric)) : [{ criterion: '', maxScore: 0 }];
    selectedStudentSerials.value = newVal.students ? [...newVal.students] : [];
    // Ensure selected students are loaded if not in the current list, especially after a search
    // This might require an additional fetch or smarter logic if selected students aren't in the initial/searched list.
    // For now, we assume `fetchAvailableStudents` on mount or empty search will cover this.
  } else {
    isEditMode.value = false;
    resetForm(); // Now this call will not throw an error
  }
  // When assignment changes, if not editing, clear search and load all students
  if (!isEditMode.value) {
      studentSearchTerm.value = '';
      fetchAvailableStudents();
  }
}, { immediate: true, deep: true });

const addCriterion = () => {
  form.value.rubric.push({ criterion: '', maxScore: 0 });
};

const removeCriterion = (index) => {
  if (form.value.rubric.length > 1) {
    form.value.rubric.splice(index, 1);
  }
};
async function handleSubmit() {
  errorMessage.value = '';
  successMessage.value = '';

  if (!form.value.title || !form.value.description || !form.value.deadline || form.value.rubric.length === 0) {
    errorMessage.value = 'Please fill in all required fields.';
    return;
  }

  for (const criterion of form.value.rubric) {
    if (!criterion.criterion || criterion.maxScore === null || criterion.maxScore < 0 || criterion.maxScore > 100) {
      errorMessage.value = 'Each rubric criterion must have a description and a score between 0 and 100.';
      return;
    }
  }

  // Assign selected students directly
  form.value.students = [...selectedStudentSerials.value];

  if (form.value.students.length === 0) {
      errorMessage.value = 'Please assign the task to at least one student.';
      return;
  }

  try {
    const payload = {
        ...form.value,
        deadline: new Date(form.value.deadline).toISOString() // Ensure ISO format for backend
    };

    if (isEditMode.value) {
      await axios.put(`${API_URL}/${props.assignment._id}`, payload, { headers: getAuthHeaders() });
      successMessage.value = 'Assignment updated successfully!';
    } else {
      await axios.post(API_URL, payload, { headers: getAuthHeaders() });
      successMessage.value = 'Assignment created successfully!';
      resetForm(); // Now this call will not throw an error
      studentSearchTerm.value = ''; // Clear search term on successful creation
      fetchAvailableStudents(); // Reload all students
    }
    emit('submitted');
  } catch (err) {
    console.error('Error submitting assignment:', err.response || err.message);
    errorMessage.value = err.response?.data?.message || 'Failed to save assignment. Please try again.';
  }
}
</script>

<style scoped>
.assignment-form-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.assignment-form-container {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.form-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px 30px;
  text-align: center;
}

.form-header h2 {
  margin: 0 0 10px 0;
  font-size: 2rem;
  font-weight: 600;
}

.form-subtitle {
  margin: 0;
  opacity: 0.9;
  font-size: 1.1rem;
}

.assignment-form {
  padding: 40px 30px;
}

.form-section {
  margin-bottom: 40px;
  padding: 25px;
  background: #f8f9fa;
  border-radius: 12px;
  border-left: 4px solid #667eea;
}

.section-title {
  color: #2c3e50;
  font-size: 1.4rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-description {
  color: #6c757d;
  margin: 0 0 20px 0;
  font-size: 0.95rem;
}

.form-group {
  margin-bottom: 25px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2c3e50;
  font-size: 1rem;
}

input[type="text"],
input[type="datetime-local"],
input[type="number"],
textarea {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 1rem;
  font-family: inherit;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

input:focus,
textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

textarea {
  resize: vertical;
  min-height: 100px;
}

.rubric-container {
  background: white;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.rubric-item {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.rubric-inputs {
  display: flex;
  gap: 15px;
  flex: 1;
}

.criterion-input {
  flex: 2;
}

.score-input {
  flex: 0 0 120px;
}

.remove-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn:hover:not(:disabled) {
  background: #c82333;
  transform: scale(1.05);
}

.remove-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  opacity: 0.5;
}

.add-criterion-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.add-criterion-btn:hover {
  background: #218838;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

.student-search-container {
  background: white;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.search-input-wrapper {
  position: relative;
  margin-bottom: 20px;
}

.search-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #6c757d;
  z-index: 1;
}

.student-search-input {
  padding-left: 45px;
  background: #f8f9fa;
  border: 2px solid #e9ecef;
}

.loading-students {
  text-align: center;
  padding: 20px;
  color: #667eea;
  font-weight: 500;
}

.info-message {
  text-align: center;
  padding: 20px;
  color: #6c757d;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.students-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  background: #f8f9fa;
}

.student-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e9ecef;
  transition: background-color 0.2s ease;
}

.student-item:last-child {
  border-bottom: none;
}

.student-item:hover {
  background: white;
}

.student-checkbox {
  margin-right: 12px;
  width: 18px;
  height: 18px;
  accent-color: #667eea;
}

.student-label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  flex: 1;
}

.student-avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.9rem;
}

.student-name {
  font-weight: 500;
  color: #2c3e50;
}

.selected-count {
  margin-top: 15px;
  padding: 10px 15px;
  background: #d4edda;
  color: #155724;
  border-radius: 6px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.message {
  padding: 15px 20px;
  border-radius: 8px;
  margin: 20px 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.success-message {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.form-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 40px;
  padding-top: 30px;
  border-top: 1px solid #e9ecef;
}

.submit-btn,
.cancel-btn {
  padding: 14px 30px;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 160px;
  justify-content: center;
}

.submit-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

.cancel-btn {
  background: #6c757d;
  color: white;
}

.cancel-btn:hover {
  background: #5a6268;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(108, 117, 125, 0.3);
}

@media (max-width: 768px) {
  .assignment-form-page {
    padding: 10px;
  }
  
  .assignment-form {
    padding: 20px 15px;
  }
  
  .form-section {
    padding: 20px 15px;
  }
  
  .rubric-inputs {
    flex-direction: column;
    gap: 10px;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .submit-btn,
  .cancel-btn {
    width: 100%;
  }
}

.info-message {
  color: #555; /* Or any other appropriate color */
  margin-top: 5px;
  display: block;
  text-align: center;
  font-style: italic;
}


</style>

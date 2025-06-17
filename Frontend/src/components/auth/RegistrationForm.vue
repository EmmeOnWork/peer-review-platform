<template>
  <div class="register-form-container">
    <h2>Peer Review Platform Registration</h2>
    <form @submit.prevent="handleRegister">
      <div class="form-group">
        <label for="name">Name</label>
        <input type="text" id="name" v-model="form.name" required />
      </div>
      <div class="form-group">
        <label for="surname">Surname</label>
        <input type="text" id="surname" v-model="form.surname" required />
      </div>
      <div class="form-group">
        <label for="email">Email</label>
        <input type="email" id="email" v-model="form.email" required />
      </div>
      <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" v-model="form.password" required />
      </div>
      <div class="form-group">
        <label for="confirmPassword">Confirm Password</label>
        <input type="password" id="confirmPassword" v-model="confirmPassword" required />
      </div>
      <div class="form-group">
        <label for="fiscalCode">Fiscal Code</label>
        <input type="text" id="fiscalCode" v-model="form.fiscalCode" required placeholder="e.g. RSSMRA85T10A562S" />
        <small class="field-hint">Insert your valid 16-character Italian fiscal code.</small>
      </div>
      <div class="form-group">
        <label for="birthDate">Birth Date</label>
        <input type="date" id="birthDate" v-model="form.birthDate" required />
      </div>
      <div class="form-group">
        <label for="residence">Residence</label>
        <input type="text" id="residence" v-model="form.residence" required />
      </div>
      <div class="form-group role-selection-wrapper">
        <label class="role-label">Role</label>
        <div class="role-selection">
          <label>
            <input type="radio" value="teacher" v-model="form.role" />
            <span class="custom-radio"></span>
            Teacher
          </label>
          <label>
            <input type="radio" value="student" v-model="form.role" />
            <span class="custom-radio"></span>
            Student
          </label>
        </div>
      </div>
      <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
      <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
      <button type="submit" class="submit-btn">Register</button>
    </form>
    <p class="login-link">
      Already have an account? <router-link to="/login">Login</router-link>
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

const form = ref({
  name: '',
  surname: '',
  email: '',
  password: '',
  fiscalCode: '',
  birthDate: '',
  residence: '',
  role: ''
});
const confirmPassword = ref('');
const errorMessage = ref('');
const successMessage = ref('');
const router = useRouter();

async function handleRegister() {
  errorMessage.value = '';
  successMessage.value = '';

  // Validazione base
  const fields = Object.values(form.value);
  if (fields.includes('') || !confirmPassword.value) {
    errorMessage.value = 'Please fill all fields and select a role.';
    return;
  }
  if (form.value.password !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match.';
    return;
  }

  try {
    // Chiamata all'endpoint /auth/register come da openapi.yaml
    await axios.post('/auth/register', {
      ...form.value
    });
    successMessage.value = 'Registration successful! You can now log in.';
    setTimeout(() => {
      router.push('/login');
    }, 1200);
  } catch (err) {
    if (err.response && err.response.data && err.response.data.message) {
      errorMessage.value = err.response.data.message;
    } else {
      errorMessage.value = 'Registration failed. Please check your data or try again.';
    }
  }
}
</script>

<style scoped>
.register-form-container {
  max-width: 450px;
  margin: 50px auto;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  background-color: #fff;
}

h2 {
  text-align: center;
  margin-bottom: 25px;
  color: #2c3e50;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: bold;
  color: #555;
}

input[type="text"],
input[type="email"],
input[type="password"],
input[type="date"] {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 1rem;
  box-sizing: border-box;
}

input:focus {
  outline: none;
  border-color: #f4b660;
  box-shadow: 0 0 0 2px rgba(244, 182, 96, 0.3);
}

.field-hint {
  font-size: 0.8rem;
  color: #888;
  margin-top: 5px;
  display: block;
}

.role-selection-wrapper {
  display: flex;
  align-items: center;
  gap: 15px;
}

.role-label {
  font-weight: bold;
  color: #555;
  width: 50px;
}

.role-selection {
  display: flex;
  gap: 20px;
}

.role-selection label {
  position: relative;
  padding-left: 30px;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  display: inline-flex;
  align-items: center;
}

.role-selection input[type="radio"] {
  position: absolute;
  opacity: 0;
  cursor: pointer;
}

.custom-radio {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  height: 18px;
  width: 18px;
  border: 2px solid #f4b660;
  border-radius: 50%;
  background: white;
  box-sizing: border-box;
}

.role-selection input[type="radio"]:checked + .custom-radio {
  background: #f4b660;
  box-shadow: inset 0 0 0 4px white;
}

.submit-btn {
  background: #f4b660;
  color: #fff;
  padding: 12px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1.1rem;
  width: 100%;
  transition: background-color 0.3s ease;
  margin-top: 10px;
}

.submit-btn:hover {
  background: #d69c39;
}

.error-message {
  color: red;
  margin-bottom: 15px;
  text-align: center;
}

.success-message {
  color: green;
  margin-bottom: 15px;
  text-align: center;
}

.login-link {
  margin-top: 20px;
  text-align: center;
  font-size: 0.9rem;
  color: #555;
}

.login-link a {
  color: #f4b660;
  text-decoration: none;
  font-weight: 600;
}

.login-link a:hover {
  text-decoration: underline;
}
</style>

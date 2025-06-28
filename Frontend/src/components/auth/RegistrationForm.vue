<template>
  <div class="registration-form-container">
    <!-- Header Section -->
    <div class="form-header">
      <div class="logo-section">
        <div class="logo-icon">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L13.09 8.26L20 9L13.09 9.74L12 16L10.91 9.74L4 9L10.91 8.26L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 12L13.09 18.26L20 19L13.09 19.74L12 26L10.91 19.74L4 19L10.91 18.26L12 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h1 class="form-title">Create Account</h1>
        <p class="form-subtitle">Join our educational platform</p>
      </div>
    </div>

    <!-- Registration Form -->
    <form @submit.prevent="register" class="registration-form">
      <div class="form-group">
         <label for="name" class="form-label">
           <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
             <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
             <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
           </svg>
           First Name
         </label>
         <input
           type="text"
           id="name"
           v-model="name"
           class="form-input"
           placeholder="Enter your first name"
           required
         />
       </div>

       <div class="form-group">
         <label for="surname" class="form-label">
           <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
             <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
             <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
           </svg>
           Last Name
         </label>
         <input
           type="text"
           id="surname"
           v-model="surname"
           class="form-input"
           placeholder="Enter your last name"
           required
         />
       </div>

      <div class="form-group">
         <label for="email" class="form-label">
           <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
             <path d="M4 4H20C21.1 4 22 4.9 22 6V18C22 19.1 21.1 20 20 20H4C2.9 20 2 19.1 2 18V6C2 4.9 2.9 4 4 4Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
             <polyline points="22,6 12,13 2,6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
           </svg>
           Email
         </label>
         <input
           type="email"
           id="email"
           v-model="email"
           class="form-input"
           placeholder="Enter your email address"
           required
         />
       </div>

       <div class="form-group">
         <label for="fiscalCode" class="form-label">
           <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
             <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
             <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
           </svg>
           Tax Code
         </label>
         <input
           type="text"
           id="fiscalCode"
           v-model="fiscalCode"
           class="form-input"
           placeholder="Enter your tax code"
           required
         />
       </div>

       <div class="form-group">
         <label for="birthDate" class="form-label">
           <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
             <rect x="3" y="4" width="18" height="18" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
             <line x1="16" y1="2" x2="16" y2="6" stroke="currentColor" stroke-width="2"/>
             <line x1="8" y1="2" x2="8" y2="6" stroke="currentColor" stroke-width="2"/>
             <line x1="3" y1="10" x2="21" y2="10" stroke="currentColor" stroke-width="2"/>
           </svg>
           Birth Date
         </label>
         <input
           type="date"
           id="birthDate"
           v-model="birthDate"
           class="form-input"
           required
         />
       </div>

       <div class="form-group">
         <label for="residence" class="form-label">
           <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
             <path d="M21 10C21 17 12 23 12 23S3 17 3 10C3 7.61305 3.94821 5.32387 5.63604 3.63604C7.32387 1.94821 9.61305 1 12 1C14.3869 1 16.6761 1.94821 18.3639 3.63604C20.0518 5.32387 21 7.61305 21 10Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
             <circle cx="12" cy="10" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
           </svg>
           Residence
         </label>
         <input
           type="text"
           id="residence"
           v-model="residence"
           class="form-input"
           placeholder="Enter your residence"
           required
         />
       </div>

      <div class="form-group">
        <label for="password" class="form-label">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="16" r="1" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M7 11V7C7 5.67392 7.52678 4.40215 8.46447 3.46447C9.40215 2.52678 10.6739 2 12 2C13.3261 2 14.5979 2.52678 15.5355 3.46447C16.4732 4.40215 17 5.67392 17 7V11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Password
        </label>
        <input
          type="password"
          id="password"
          v-model="password"
          class="form-input"
          placeholder="Create a secure password"
          required
        />
      </div>

      <div class="form-group">
        <label for="confirmPassword" class="form-label">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="16" r="1" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M7 11V7C7 5.67392 7.52678 4.40215 8.46447 3.46447C9.40215 2.52678 10.6739 2 12 2C13.3261 2 14.5979 2.52678 15.5355 3.46447C16.4732 4.40215 17 5.67392 17 7V11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Confirm Password
        </label>
        <input
          type="password"
          id="confirmPassword"
          v-model="confirmPassword"
          class="form-input"
          placeholder="Confirm your password"
          required
        />
      </div>

      <div class="form-group">
        <label for="role" class="form-label">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 21V19C16 17.9391 15.5786 16.9217 14.8284 16.1716C14.0783 15.4214 13.0609 15 12 15H5C3.93913 15 2.92172 15.4214 2.17157 16.1716C1.42143 16.9217 1 17.9391 1 19V21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="8.5" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="17,11 19,13 23,9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Role
        </label>
        <select id="role" v-model="role" class="form-select" required>
          <option value="">Select your role</option>
          <option value="student">Student</option>
          <option value="teacher">Teacher</option>
        </select>
      </div>

      <div v-if="errorMessage" class="error-message">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ errorMessage }}
      </div>

      <button type="submit" class="submit-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M22 12H16L14 15H10L8 12H2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M5.45 5.11L2 12V18C2 18.5304 2.21071 19.0391 2.58579 19.4142C2.96086 19.7893 3.46957 20 4 20H20C20.5304 20 21.0391 19.7893 21.4142 19.4142C21.7893 19.0391 22 18.5304 22 18V12L18.55 5.11C18.3844 4.77679 18.1292 4.49637 17.813 4.30028C17.4967 4.10419 17.1321 4.0002 16.76 4H7.24C6.86792 4.0002 6.50326 4.10419 6.18704 4.30028C5.87083 4.49637 5.61558 4.77679 5.45 5.11Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Create Account
      </button>
    </form>

    <!-- Footer -->
    <div class="form-footer">
      <p class="login-link">
        Already have an account? 
        <router-link to="/login" class="login-link-btn">Log in here</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

// Reactive variables for form fields
const name = ref('');
const surname = ref('');
const email = ref('');
const fiscalCode = ref('');
const birthDate = ref('');
const residence = ref('');
const password = ref('');
const confirmPassword = ref('');
const role = ref('user'); // Default role
const errorMessage = ref('');

const router = useRouter();

async function register() {
  // Reset error message
  errorMessage.value = '';
  
  // Validate password match
  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match';
    return;
  }

  try {
    const response = await fetch('/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: name.value,
        surname: surname.value,
        email: email.value,
        fiscalCode: fiscalCode.value,
        birthDate: birthDate.value,
        residence: residence.value,
        password: password.value,
        role: role.value,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      errorMessage.value = data.message || 'Error during registration';
      return;
    }

    // Registration successful, redirect to login
    router.push('/login');
  } catch (error) {
    errorMessage.value = 'Connection error';
    console.error('Registration error:', error);
  }
}
</script>

<style scoped>
.registration-form-container {
  max-width: 500px;
  margin: 0 auto;
  padding: 0;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  background-color: #ffffff;
  overflow: hidden;
  border: 1px solid #f1f3f4;
}

.form-header {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  padding: 40px 30px;
  text-align: center;
  color: white;
}

.logo-section {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.logo-icon {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  padding: 15px;
  margin-bottom: 20px;
  backdrop-filter: blur(10px);
}

.form-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: white;
}

.form-subtitle {
  font-size: 1rem;
  margin: 0;
  opacity: 0.9;
  color: rgba(255, 255, 255, 0.9);
}

.registration-form {
  padding: 40px 30px 30px;
}

.form-group {
  margin-bottom: 25px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.95rem;
}

.form-input,
.form-select {
  width: 100%;
  padding: 15px 18px;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  font-size: 1rem;
  box-sizing: border-box;
  transition: all 0.3s ease;
  background-color: #f8f9fa;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #4facfe;
  box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.1);
  background-color: #ffffff;
  transform: translateY(-1px);
}

.form-input::placeholder {
  color: #adb5bd;
  font-size: 0.95rem;
}

.form-select {
  cursor: pointer;
}

.form-select option {
  padding: 10px;
}

.submit-btn {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: #ffffff;
  padding: 16px 24px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 1.1rem;
  font-weight: 600;
  width: 100%;
  transition: all 0.3s ease;
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 8px 25px rgba(79, 172, 254, 0.3);
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(79, 172, 254, 0.4);
  background: linear-gradient(135deg, #3d8bfe 0%, #00d4fe 100%);
}

.submit-btn:active {
  transform: translateY(0);
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e74c3c;
  background-color: #fdf2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 20px;
  font-size: 0.9rem;
  font-weight: 500;
}

.form-footer {
  padding: 20px 30px 30px;
  text-align: center;
  border-top: 1px solid #f1f3f4;
  background-color: #fafbfc;
}

.login-link {
  margin: 0;
  font-size: 0.95rem;
  color: #6c757d;
}

.login-link-btn {
  color: #4facfe;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
}

.login-link-btn:hover {
  color: #3d8bfe;
  text-decoration: underline;
}

/* Responsive Design */
@media (max-width: 480px) {
  .registration-form-container {
    max-width: 95%;
    margin: 20px auto;
  }
  
  .form-header {
    padding: 30px 20px;
  }
  
  .form-title {
    font-size: 1.6rem;
  }
  
  .form-subtitle {
    font-size: 0.9rem;
  }
  
  .registration-form {
    padding: 30px 20px 20px;
  }
  
  .form-footer {
    padding: 15px 20px 25px;
  }
}
</style>

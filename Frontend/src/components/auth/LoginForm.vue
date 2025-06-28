<template>
  <div class="login-form-container">
    <div class="form-header">
      <div class="logo-section">
        <div class="logo-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L13.09 8.26L20 9L13.09 9.74L12 16L10.91 9.74L4 9L10.91 8.26L12 2Z" fill="#667eea"/>
            <path d="M19 15L20.25 18.5L24 19L20.25 19.5L19 23L17.75 19.5L14 19L17.75 18.5L19 15Z" fill="#667eea"/>
            <path d="M5 15L6.25 18.5L10 19L6.25 19.5L5 23L3.75 19.5L0 19L3.75 18.5L5 15Z" fill="#667eea"/>
          </svg>
        </div>
        <h2 class="form-title">Welcome Back</h2>
        <p class="form-subtitle">Sign in to your PeerReview account</p>
      </div>
    </div>
    
    <form @submit.prevent="submitLogin" class="login-form">
      <div class="form-group">
        <label for="email" class="form-label">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 4H20C21.1 4 22 4.9 22 6V18C22 19.1 21.1 20 20 20H4C2.9 20 2 19.1 2 18V6C2 4.9 2.9 4 4 4Z" stroke="#7f8c8d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M22 6L12 13L2 6" stroke="#7f8c8d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Email Address
        </label>
        <input
          type="email"
          id="email"
          v-model="email"
          required
          placeholder="Enter your email address"
          class="form-input"
        />
      </div>
      
      <div class="form-group">
        <label for="password" class="form-label">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="#7f8c8d" stroke-width="2"/>
            <circle cx="12" cy="16" r="1" fill="#7f8c8d"/>
            <path d="M7 11V7C7 5.67392 7.52678 4.40215 8.46447 3.46447C9.40215 2.52678 10.6739 2 12 2C13.3261 2 14.5979 2.52678 15.5355 3.46447C16.4732 4.40215 17 5.67392 17 7V11" stroke="#7f8c8d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Password
        </label>
        <input
          type="password"
          id="password"
          v-model="password"
          required
          placeholder="Enter your password"
          class="form-input"
        />
      </div>
      
      <div v-if="errorMessage" class="error-message">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="12" cy="12" r="10" stroke="#e74c3c" stroke-width="2"/>
          <line x1="15" y1="9" x2="9" y2="15" stroke="#e74c3c" stroke-width="2"/>
          <line x1="9" y1="9" x2="15" y2="15" stroke="#e74c3c" stroke-width="2"/>
        </svg>
        {{ errorMessage }}
      </div>
      
      <button type="submit" class="submit-btn">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M15 3H6C4.9 3 4 3.9 4 5V19C4 20.1 4.9 21 6 21H15C16.1 21 17 20.1 17 19V5C17 3.9 16.1 3 15 3Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M21 9L17 5L21 1" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Sign In
      </button>
    </form>
    
    <div class="form-footer">
      <p class="register-link">
        Don't have an account? 
        <router-link to="/register" class="register-link-btn">Create one here</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useStore } from "vuex"; // Aggiungi questo

export default {
  name: "LoginForm",
  setup() {
    const email = ref("");
    const password = ref("");
    const errorMessage = ref("");
    const router = useRouter();
    const store = useStore(); // Aggiungi questo

    const submitLogin = async () => {
      try {
        // Chiamata all'endpoint /auth/login come da openapi.yaml
        const response = await axios.post("/auth/login", {
          email: email.value,
          password: password.value,
        });

        // Usa lo store invece del localStorage diretto
        store.dispatch('login', {
          token: response.data.token,
          user: response.data.user
        });

        // Redirect in base al ruolo
        if (response.data.user.role === "teacher") {
          router.push("/teacher/dashboard");
        } else if (response.data.user.role === "student") {
          router.push("/student/dashboard");
        } else {
          router.push("/");
        }
      } catch (err) {
        errorMessage.value = "Invalid credentials or network error.";
      }
    };

    return {
      email,
      password,
      errorMessage,
      submitLogin,
    };
  },
};
</script>

<style scoped>
.login-form-container {
  max-width: 450px;
  margin: 0 auto;
  padding: 0;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  background-color: #ffffff;
  overflow: hidden;
  border: 1px solid #f1f3f4;
}

.form-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

.login-form {
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

.form-input {
  width: 100%;
  padding: 15px 18px;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  font-size: 1rem;
  box-sizing: border-box;
  transition: all 0.3s ease;
  background-color: #f8f9fa;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  background-color: #ffffff;
  transform: translateY(-1px);
}

.form-input::placeholder {
  color: #adb5bd;
  font-size: 0.95rem;
}

.submit-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(102, 126, 234, 0.4);
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
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

.register-link {
  margin: 0;
  font-size: 0.95rem;
  color: #6c757d;
}

.register-link-btn {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
}

.register-link-btn:hover {
  color: #5a6fd8;
  text-decoration: underline;
}

/* Responsive Design */
@media (max-width: 480px) {
  .login-form-container {
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
  
  .login-form {
    padding: 30px 20px 20px;
  }
  
  .form-footer {
    padding: 15px 20px 25px;
  }
}
</style>

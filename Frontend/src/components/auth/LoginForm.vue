<template>
  <div class="login-form-container">
    <h2>Platform Login</h2>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label for="email">Email</label>
        <input
          type="email"
          id="email"
          v-model="email"
          required
          placeholder="e.g. user@example.com"
        />
      </div>
      <div class="form-group">
        <label for="password">Assword</label>
        <input
          type="password"
          id="password"
          v-model="password"
          required
          placeholder="Enter your password"
        />
      </div>
      <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
      <button type="submit" class="submit-btn">Login</button>
    </form>
    <p class="register-link">
      Don't have an account? <router-link to="/register">Register here</router-link>
    </p>
  </div>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";

const email = ref("");
const password = ref("");
const errorMessage = ref("");
const router = useRouter();

async function handleLogin() {
  errorMessage.value = "";

  if (!email.value || !password.value) {
    errorMessage.value = "Please fill all fields.";
    return;
  }

  try {
    // Chiamata all'endpoint /auth/login come da openapi.yaml
    const response = await axios.post("/auth/login", {
      email: email.value,
      password: password.value,
    });

    // Salva il token e il ruolo in localStorage
    localStorage.setItem("userToken", response.data.token);
    localStorage.setItem("userRole", response.data.user.role);

    // Redirect in base al ruolo
    if (response.data.user.role === "teacher") {
      router.push("/teacher/dashboard");
    } else if (response.data.user.role === "student") {
      router.push("/student/dashboard");
    } else {
      router.push("/");
    }
  } catch (err) {
    errorMessage.value = "Credenziali non valide o errore di rete.";
  }
}
</script>

<style scoped>
.login-form-container {
  max-width: 400px;
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

input[type="email"],
input[type="password"] {
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

.register-link {
  margin-top: 20px;
  text-align: center;
  font-size: 0.9rem;
  color: #555;
}

.register-link a {
  color: #f4b660;
  text-decoration: none;
  font-weight: 600;
}

.register-link a:hover {
  text-decoration: underline;
}
</style>

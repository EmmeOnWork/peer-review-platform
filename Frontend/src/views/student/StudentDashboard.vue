<template>
  <div class="dashboard-container">
    <div class="header-section">
      <h1 class="dashboard-title">Student Dashboard</h1>
      <p class="welcome-message">Welcome back, <span class="user-name">{{ user?.name }}</span>!</p>
    </div>
    
    <div class="dashboard-grid">
      <!-- Profile Card -->
      <div class="dashboard-card profile-card">
        <div class="card-icon">
          <!-- SVG omitted for brevity -->
        </div>
        <h3 class="card-title">My Profile</h3>
        <p class="card-description">Manage your personal information and settings</p>
        <router-link to="/profile" class="card-button">View Profile</router-link>
      </div>

      <!-- Assignments Card -->
      <div class="dashboard-card assignments-card">
        <div class="card-icon">
          <!-- SVG omitted for brevity -->
        </div>
        <h3 class="card-title">View Assignments</h3>
        <p class="card-description">Browse and work on your course assignments</p>
        <router-link to="/student/assignments" class="card-button">View Assignments</router-link>
      </div>
    </div>

    <div class="logout-section">
      <button @click="logoutUser" class="logout-button">
        <!-- SVG omitted for brevity -->
        Logout
      </button>
    </div>
  </div>
</template>


<script setup>
import { computed } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';

const store = useStore();
const router = useRouter();

const user = computed(() => store.state.user);

const logoutUser = async () => {
  try {
    await store.dispatch('logout');
    router.push('/login');
  } catch (error) {
    console.error('Logout failed:', error);
    // Handle logout error
  }
};
</script>

<style scoped>
.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
  background-color: #ffffff;
  min-height: 100vh;
}

.header-section {
  text-align: center;
  margin-bottom: 40px;
  padding: 20px 0;
}

.dashboard-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-message {
  font-size: 1.2rem;
  color: #7f8c8d;
  margin: 0;
}

.user-name {
  font-weight: 600;
  color: #3498db;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 25px;
  margin-bottom: 40px;
}

.dashboard-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 30px 25px;
  text-align: center;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border: 1px solid #f1f3f4;
  position: relative;
  overflow: hidden;
}

.dashboard-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea, #764ba2);
}

.dashboard-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
}

.profile-card::before {
  background: linear-gradient(90deg, #4A90E2, #357ABD);
}

.assignments-card::before {
  background: linear-gradient(90deg, #50C878, #3CB371);
}

.submissions-card::before {
  background: linear-gradient(90deg, #FF6B6B, #FF5252);
}

.reviews-card::before {
  background: linear-gradient(90deg, #9B59B6, #8E44AD);
}

.card-icon {
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 80px;
  height: 80px;
  background: #f8f9fa;
  border-radius: 50%;
  margin: 0 auto 20px;
  transition: all 0.3s ease;
}

.dashboard-card:hover .card-icon {
  transform: scale(1.1);
  background: #e9ecef;
}

.card-title {
  font-size: 1.4rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 12px;
}

.card-description {
  font-size: 0.95rem;
  color: #7f8c8d;
  line-height: 1.5;
  margin-bottom: 25px;
}

.card-button {
  display: inline-block;
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-decoration: none;
  border-radius: 25px;
  font-weight: 500;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.card-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  text-decoration: none;
  color: white;
}

.profile-card .card-button {
  background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
  box-shadow: 0 4px 15px rgba(74, 144, 226, 0.3);
}

.assignments-card .card-button {
  background: linear-gradient(135deg, #50C878 0%, #3CB371 100%);
  box-shadow: 0 4px 15px rgba(80, 200, 120, 0.3);
}

.submissions-card .card-button {
  background: linear-gradient(135deg, #FF6B6B 0%, #FF5252 100%);
  box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
}

.reviews-card .card-button {
  background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%);
  box-shadow: 0 4px 15px rgba(155, 89, 182, 0.3);
}

.logout-section {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #ecf0f1;
}

.logout-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
  color: white;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
}

.logout-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(231, 76, 60, 0.4);
  background: linear-gradient(135deg, #c0392b 0%, #a93226 100%);
}

/* Responsive Design */
@media (max-width: 768px) {
  .dashboard-container {
    padding: 20px 15px;
  }
  
  .dashboard-title {
    font-size: 2rem;
  }
  
  .dashboard-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .dashboard-card {
    padding: 25px 20px;
  }
}

@media (max-width: 480px) {
  .dashboard-title {
    font-size: 1.8rem;
  }
  
  .welcome-message {
    font-size: 1rem;
  }
  
  .card-title {
    font-size: 1.2rem;
  }
  
  .card-description {
    font-size: 0.9rem;
  }
}
</style>


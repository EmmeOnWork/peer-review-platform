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
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 12C14.7614 12 17 9.76142 17 7C17 4.23858 14.7614 2 12 2C9.23858 2 7 4.23858 7 7C7 9.76142 9.23858 12 12 12Z" fill="#4A90E2"/>
            <path d="M12 14C7.58172 14 4 17.5817 4 22H20C20 17.5817 16.4183 14 12 14Z" fill="#4A90E2"/>
          </svg>
        </div>
        <h3 class="card-title">My Profile</h3>
        <p class="card-description">Manage your personal information and settings</p>
        <router-link to="/profile" class="card-button">View Profile</router-link>
      </div>
    </div>

    <div class="logout-section">
      <button @click="logoutUser" class="logout-button">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M17 7L15.59 8.41L18.17 11H8V13H18.17L15.59 15.59L17 17L22 12L17 7Z" fill="white"/>
          <path d="M19 19H5V5H19V3H5C3.89 3 3 3.89 3 5V19C3 20.1 3.89 21 5 21H19C20.1 21 21 20.1 21 19V17H19V19Z" fill="white"/>
        </svg>
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
  justify-items: center;
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
  max-width: 350px;
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

.logout-section {
  text-align: center;
  margin-top: 40px;
}

.logout-button {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 30px;
  background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
  color: white;
  border: none;
  border-radius: 25px;
  font-weight: 500;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
}

.logout-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(231, 76, 60, 0.4);
}

.logout-button:active {
  transform: translateY(0);
}

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
</style>


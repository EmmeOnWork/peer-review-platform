<template>
  <div class="profile-page">
    <div class="profile-container">
      <!-- Profile Header -->
      <div class="profile-header">
        <div class="profile-avatar">
          <i class="fas fa-user"></i>
        </div>
        <h2>Your Profile</h2>
        <p class="profile-subtitle">Manage your account information and settings</p>
      </div>

      <!-- Main Content -->
      <div class="profile-content">
        <!-- Profile Information Card -->
        <div class="profile-info-card">
          <div v-if="loading" class="loading-state">
            <i class="fas fa-spinner fa-spin"></i>
            <span>Loading your profile...</span>
          </div>
          
          <div v-else class="profile-details">
            <div class="profile-fields">
              <div class="profile-field">
                <div class="field-icon"><i class="fas fa-user"></i></div>
                <div class="field-content">
                  <strong>Name</strong>
                  <span>{{ user.name }}</span>
                </div>
              </div>
              
              <div class="profile-field">
                <div class="field-icon"><i class="fas fa-user-tag"></i></div>
                <div class="field-content">
                  <strong>Surname</strong>
                  <span>{{ user.surname }}</span>
                </div>
              </div>
              
              <div class="profile-field">
                <div class="field-icon"><i class="fas fa-envelope"></i></div>
                <div class="field-content">
                  <strong>Email</strong>
                  <span>{{ user.email }}</span>
                </div>
              </div>
              
              <div class="profile-field">
                <div class="field-icon"><i class="fas fa-user-shield"></i></div>
                <div class="field-content">
                  <strong>Role</strong>
                  <span class="role-badge" :class="user.role?.toLowerCase()">{{ user.role }}</span>
                </div>
              </div>
              
              <div class="profile-field">
                <div class="field-icon"><i class="fas fa-id-card"></i></div>
                <div class="field-content">
                  <strong>Fiscal Code</strong>
                  <span>{{ user.fiscalCode }}</span>
                </div>
              </div>
              
              <div class="profile-field">
                <div class="field-icon"><i class="fas fa-calendar"></i></div>
                <div class="field-content">
                  <strong>Birth Date</strong>
                  <span>{{ user.birthDate ? new Date(user.birthDate).toLocaleDateString() : 'N/A' }}</span>
                </div>
              </div>
              
              <div class="profile-field">
                <div class="field-icon"><i class="fas fa-home"></i></div>
                <div class="field-content">
                  <strong>Residence</strong>
                  <span>{{ user.residence }}</span>
                </div>
              </div>
              
              <div class="profile-field" v-if="user.serialNumber">
                <div class="field-icon"><i class="fas fa-hashtag"></i></div>
                <div class="field-content">
                  <strong>Serial Number</strong>
                  <span>{{ user.serialNumber }}</span>
                </div>
              </div>
            </div>
            
            <div v-if="errorMessage && !editing" class="message error-message">
              <i class="fas fa-exclamation-triangle"></i>
              {{ errorMessage }}
            </div>

            <div class="action-buttons">
              <button class="btn edit-btn" @click="editing = !editing">
                <i class="fas" :class="editing ? 'fa-times' : 'fa-edit'"></i>
                {{ editing ? 'Cancel' : 'Edit Profile' }}
              </button>
              <button class="btn logout-btn" @click="handleLogout">
                <i class="fas fa-sign-out-alt"></i>
                Logout
              </button>
            </div>
          </div>
        </div>

        <!-- Edit Panel -->
        <transition name="slide-in">
          <div v-if="editing" class="edit-panel">
            <div class="edit-panel-header">
              <h3><i class="fas fa-edit"></i> Edit Your Information</h3>
            </div>
            
            <div class="edit-panel-content">
              <!-- Residence Update Form -->
              <form @submit.prevent="handleResidenceUpdate" class="edit-form">
                <div class="form-section">
                  <h4><i class="fas fa-home"></i> Update Residence</h4>
                  <div class="form-group">
                    <label for="residence">New residence</label>
                    <input type="text" id="residence" v-model="editResidence" required placeholder="Enter your new residence" />
                  </div>
                  <button type="submit" class="btn save-btn">
                    <i class="fas fa-save"></i> Save residence
                  </button>
                  <div v-if="residenceSuccess" class="message success-message">
                    <i class="fas fa-check-circle"></i> {{ residenceSuccess }}
                  </div>
                  <div v-if="residenceError" class="message error-message">
                    <i class="fas fa-exclamation-triangle"></i> {{ residenceError }}
                  </div>
                </div>
              </form>

              <div class="form-separator"></div>

              <!-- Password Update Form -->
              <form @submit.prevent="handlePasswordUpdate" class="edit-form">
                <div class="form-section">
                  <h4><i class="fas fa-lock"></i> Change Password</h4>
                  <div class="form-group">
                    <label for="oldPassword">Current password</label>
                    <input type="password" id="oldPassword" v-model="oldPassword" required placeholder="Enter current password" />
                  </div>
                  <div class="form-group">
                    <label for="newPassword">New password</label>
                    <input type="password" id="newPassword" v-model="newPassword" required placeholder="Enter new password" />
                  </div>
                  <div class="form-group">
                    <label for="confirmPassword">Confirm new password</label>
                    <input type="password" id="confirmPassword" v-model="confirmPassword" required placeholder="Confirm new password" />
                  </div>
                  <button type="submit" class="btn save-btn">
                    <i class="fas fa-key"></i> Change password
                  </button>
                  <div v-if="passwordSuccess" class="message success-message">
                    <i class="fas fa-check-circle"></i> {{ passwordSuccess }}
                  </div>
                  <div v-if="passwordError" class="message error-message">
                    <i class="fas fa-exclamation-triangle"></i> {{ passwordError }}
                  </div>
                </div>
              </form>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";
import { useRouter } from "vue-router";

const user = ref({});
const loading = ref(true);
const errorMessage = ref("");
const editing = ref(false);
const router = useRouter();

// Residence update state
const editResidence = ref("");
const residenceSuccess = ref("");
const residenceError = ref("");

// Password update state
const oldPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const passwordSuccess = ref("");
const passwordError = ref("");

// Fetch user profile
async function fetchProfile() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const token = localStorage.getItem("userToken");
    if (!token) {
      errorMessage.value = "Authentication token not found. Please log in.";
      // Consider redirecting or showing a login button
      // router.push("/login");
      loading.value = false;
      return;
    }
    const response = await axios.get("/auth/users/me", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    user.value = response.data;
    if (response.data && response.data.residence !== undefined) {
        editResidence.value = response.data.residence;
    } else {
        editResidence.value = ""; // Fallback
    }
  } catch (error) {
    console.error("Profile fetch error:", error);
    if (error.response) {
      errorMessage.value = `Failed to load profile: ${error.response.data?.message || error.response.statusText}`;
      if (error.response.status === 401) {
        // Potresti voler reindirizzare o mostrare un messaggio specifico per il 401
        // errorMessage.value = "Session expired. Please log in again.";
      }
    } else if (error.request) {
      errorMessage.value = "No response from server. Check connection.";
    } else {
      errorMessage.value = "Error setting up request.";
    }
    user.value = {}; // Pulisci i dati utente in caso di errore
  } finally {
    loading.value = false;
  }
}

// Update residence only
async function handleResidenceUpdate() {
  residenceSuccess.value = "";
  residenceError.value = "";
  if (user.value && editResidence.value === user.value.residence) {
    residenceError.value = "Residence is unchanged.";
    return;
  }
  if (!editResidence.value.trim()) {
    residenceError.value = "New residence cannot be empty.";
    return;
  }
  try {
    await axios.put("/auth/users/me", { residence: editResidence.value }, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("userToken")}`,
      },
    });
    residenceSuccess.value = "Residence updated successfully!";
    await fetchProfile(); // Ricarica i dati del profilo dopo l'aggiornamento
  } catch (err) {
    console.error("Residence update error:", err);
    residenceError.value =
      err.response?.data?.message || "Error updating residence.";
  }
}

// Update password
async function handlePasswordUpdate() {
  passwordSuccess.value = "";
  passwordError.value = "";

  if (!oldPassword.value || !newPassword.value || !confirmPassword.value) {
    passwordError.value = "Please fill all password fields.";
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = "New passwords do not match.";
    return;
  }
  if (newPassword.value.length < 8) {
    passwordError.value = "New password must be at least 8 characters.";
    return;
  }
  if (oldPassword.value === newPassword.value) {
    passwordError.value = "New password must be different from the old one.";
    return;
  }

  try {
    await axios.put("/auth/users/me", {
      password: newPassword.value,
      old_password: oldPassword.value, // Assicurati che il backend si aspetti 'old_password'
    }, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("userToken")}`,
      },
    });
    passwordSuccess.value = "Password changed successfully!";
    oldPassword.value = "";
    newPassword.value = "";
    confirmPassword.value = "";
  } catch (err) {
    console.error("Password update error:", err);
    passwordError.value =
      err.response?.data?.message || "Error updating password.";
  }
}

// Logout with backend call
async function handleLogout() {
  try {
    await axios.post("/auth/logout", {}, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("userToken")}`,
      },
    });
  } catch (e) {
    console.warn("Logout API call failed, proceeding with local logout:", e);
    // Even if logout fails on backend, clear local storage and redirect
  }
  localStorage.removeItem("userToken");
  localStorage.removeItem("userRole"); // Se lo usi
  user.value = {}; // Pulisci i dati utente dallo stato
  router.push("/login");
}

onMounted(() => {
  fetchProfile();
});
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.profile-container {
  max-width: 1200px;
  margin: 0 auto;
}

.profile-header {
  text-align: center;
  margin-bottom: 40px;
  background: white;
  padding: 40px 30px;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.profile-avatar {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  color: white;
  font-size: 2rem;
}

.profile-header h2 {
  color: #2c3e50;
  font-size: 2.2rem;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.profile-subtitle {
  color: #6c757d;
  font-size: 1.1rem;
  margin: 0;
}

.profile-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 30px;
}

@media (min-width: 1024px) {
  .profile-content {
    grid-template-columns: 2fr 1fr;
  }
}

.profile-info-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 30px;
  color: #667eea;
  font-size: 1.1rem;
  gap: 15px;
}

.loading-state i {
  font-size: 2rem;
}

.profile-details {
  padding: 40px 30px;
}

.profile-fields {
  margin-bottom: 30px;
}

.profile-field {
  display: flex;
  align-items: center;
  padding: 20px 0;
  border-bottom: 1px solid #f1f3f4;
  gap: 20px;
}

.profile-field:last-child {
  border-bottom: none;
}

.field-icon {
  width: 40px;
  height: 40px;
  background: #f8f9fa;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667eea;
  font-size: 1.1rem;
  flex-shrink: 0;
}

.field-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.field-content strong {
  color: #2c3e50;
  font-weight: 600;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.field-content span {
  color: #495057;
  font-size: 1.1rem;
  font-weight: 500;
}

.role-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.role-badge.teacher {
  background: #e3f2fd;
  color: #1976d2;
}

.role-badge.student {
  background: #f3e5f5;
  color: #7b1fa2;
}

.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
  padding-top: 30px;
  border-top: 1px solid #f1f3f4;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 140px;
  justify-content: center;
}

.edit-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.edit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

.logout-btn {
  background: #dc3545;
  color: white;
}

.logout-btn:hover {
  background: #c82333;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(220, 53, 69, 0.3);
}

.save-btn {
  background: #28a745;
  color: white;
  width: 100%;
  margin-top: 15px;
}

.save-btn:hover {
  background: #218838;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(40, 167, 69, 0.3);
}

.edit-panel {
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.edit-panel-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 25px 30px;
}

.edit-panel-header h3 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}

.edit-panel-content {
  padding: 30px;
}

.edit-form {
  width: 100%;
}

.form-section {
  margin-bottom: 30px;
}

.form-section h4 {
  color: #2c3e50;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0 0 20px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.95rem;
}

input[type="text"],
input[type="password"] {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 1rem;
  font-family: inherit;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-separator {
  height: 1px;
  background: #e9ecef;
  margin: 40px 0;
}

.message {
  padding: 12px 16px;
  border-radius: 8px;
  margin-top: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
}

.success-message {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.slide-in-enter-active,
.slide-in-leave-active {
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.slide-in-enter-from,
.slide-in-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

@media (max-width: 768px) {
  .profile-page {
    padding: 10px;
  }
  
  .profile-header {
    padding: 30px 20px;
  }
  
  .profile-details,
  .edit-panel-content {
    padding: 20px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
  
  .profile-field {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .field-content {
    width: 100%;
  }
}
</style>
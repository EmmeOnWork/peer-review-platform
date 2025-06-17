<template>
  <div class="profile-page-background"> <!-- Sostituisce .profile-outer -->
    <div class="profile-layout-container"> <!-- Contenitore per layout a due colonne -->

      <!-- Profile Information Card (sostituisce .profile-container per la parte info) -->
      <div class="profile-info-card">
        <h2>Your Profile</h2>
        <div v-if="loading" class="loading-placeholder">Loading...</div>
        <div v-else>
          <div class="profile-fields">
            <div class="profile-field"><strong>Name:</strong> <span>{{ user.name }}</span></div>
            <div class="profile-field"><strong>Surname:</strong> <span>{{ user.surname }}</span></div>
            <div class="profile-field"><strong>Email:</strong> <span>{{ user.email }}</span></div>
            <div class="profile-field"><strong>Role:</strong> <span>{{ user.role }}</span></div>
            <div class="profile-field"><strong>Fiscal Code:</strong> <span>{{ user.fiscalCode }}</span></div>
            <div class="profile-field"><strong>Birth Date:</strong> <span>{{ user.birthDate ? new Date(user.birthDate).toLocaleDateString() : 'N/A' }}</span></div>
            <div class="profile-field"><strong>Residence:</strong> <span>{{ user.residence }}</span></div>
            <div class="profile-field" v-if="user.serialNumber"><strong>Serial Number:</strong> <span>{{ user.serialNumber }}</span></div>
          </div>
          
          <!-- Messaggio di errore principale, se presente -->
          <div v-if="errorMessage && !editing" class="message error-message main-error">{{ errorMessage }}</div>

          <!-- Bottoni centrati come nel tuo originale, ma con nuove classi -->
          <div class="action-buttons"> <!-- Sostituisce .center-btns -->
            <button class="btn modify-btn" @click="editing = !editing"> <!-- Sostituisce .edit-btn -->
              {{ editing ? 'Cancel' : 'Edit Profile' }}
            </button>
            <button class="btn danger-btn" @click="handleLogout">Logout</button> <!-- Sostituisce .logout-btn (ora danger-btn per coerenza) -->
          </div>
        </div>
      </div>

      <!-- Editing Panel Card (sostituisce .edit-form-dropdown.right-dropdown) -->
      <transition name="slide-from-right"> <!-- Transizione aggiornata -->
        <div v-if="editing" class="edit-panel-card">
          <h3>Edit Your Information</h3> <!-- Titolo per il pannello di modifica -->
          
          <!-- Residence Update Form -->
          <form @submit.prevent="handleResidenceUpdate" class="edit-form-section"> <!-- Sostituisce .edit-form -->
            <h4>Update Residence</h4> <!-- Sottotitolo per sezione -->
            <div class="form-group">
              <label for="residence">New residence</label>
              <input type="text" id="residence" v-model="editResidence" required />
            </div>
            <button type="submit" class="btn save-btn">Save residence</button> <!-- Mantiene .save-btn -->
            <div v-if="residenceSuccess" class="message success-message">{{ residenceSuccess }}</div>
            <div v-if="residenceError" class="message error-message">{{ residenceError }}</div>
          </form>

          <hr class="form-separator" />

          <!-- Password Update Form -->
          <form @submit.prevent="handlePasswordUpdate" class="edit-form-section"> <!-- Sostituisce .edit-form -->
            <h4>Change Password</h4> <!-- Sottotitolo per sezione -->
            <div class="form-group">
              <label for="oldPassword">Current password</label>
              <input type="password" id="oldPassword" v-model="oldPassword" required />
            </div>
            <div class="form-group">
              <label for="newPassword">New password</label>
              <input type="password" id="newPassword" v-model="newPassword" required />
            </div>
            <div class="form-group">
              <label for="confirmPassword">Confirm new password</label>
              <input type="password" id="confirmPassword" v-model="confirmPassword" required />
            </div>
            <button type="submit" class="btn save-btn">Change password</button> <!-- Mantiene .save-btn -->
            <div v-if="passwordSuccess" class="message success-message">{{ passwordSuccess }}</div>
            <div v-if="passwordError" class="message error-message">{{ passwordError }}</div>
          </form>
        </div>
      </transition>
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
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

:root { 
  --primary-color: #f4b660;
  --primary-hover-color: #e0a850; 
  --danger-color: #e74c3c; 
  --danger-hover-color: #c0392b;
  --success-color: #2ecc71; /* Verde per i messaggi di successo */
  --success-text-color: #27ae60; /* Testo per messaggi di successo */
  --error-text-color: #c0392b; /* Testo per messaggi di errore */
  --text-primary: #2c3e50;
  --text-secondary: #555;
  --bg-light: #f8f9fa; /* Sfondo pagina come da richiesta */
  --bg-white: #ffffff; /* Sfondo card */
  --border-color: #cccccc; 
  --card-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
  --input-focus-shadow: 0 0 0 3px rgba(244, 182, 96, 0.4);
  --border-radius-md: 8px;
  --border-radius-lg: 12px;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.profile-page-background {
  min-height: 100vh;
  display: flex;
  align-items: flex-start; /* Allinea le card in alto */
  justify-content: center;
  background-color: var(--bg-light, #f8f9fa);
  padding: 40px 20px;
  font-family: 'Poppins', sans-serif;
}

.profile-layout-container {
  display: flex;
  flex-wrap: wrap;
  gap: 30px;
  width: 100%;
  max-width: 1000px; /* O la larghezza che preferisci per il layout a due colonne */
  align-items: flex-start;
}

.profile-info-card,
.edit-panel-card {
  background-color: var(--bg-white, #ffffff);
  border-radius: var(--border-radius-lg, 12px);
  box-shadow: var(--card-shadow, 0 8px 25px rgba(0, 0, 0, 0.08));
  padding: 30px 35px;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color, #cccccc);
}

.profile-info-card {
  flex: 1; 
  min-width: 320px;
}

.edit-panel-card { /* Questo sostituisce .edit-form-dropdown.right-dropdown */
  width: 100%; 
  max-width: 400px; 
  flex-shrink: 0;
  /* Non più position:absolute, ma parte del flusso flex */
}

@media (min-width: 860px) { /* Adatta questo breakpoint se necessario */
  /* Stili specifici per quando il layout è a due colonne */
}

h2, h3, h4 {
  color: var(--text-primary, #2c3e50);
  margin-bottom: 25px;
  font-weight: 600;
}
h2 { /* Titolo principale del profilo */
  font-size: 1.8rem;
  text-align: center; /* Come nel tuo originale */
  width: 100%;
}
h3 { /* Titolo del pannello di modifica */
  font-size: 1.5rem;
  text-align: center;
  border-bottom: 1px solid var(--border-color, #cccccc);
  padding-bottom: 15px;
}
h4 { /* Sottotitoli nei form */
  font-size: 1.2rem;
  color: var(--text-secondary, #555);
  margin-bottom: 20px;
  text-align: left;
}

.loading-placeholder { /* Stile per il messaggio di caricamento */
  text-align: center;
  padding: 40px 0;
  color: var(--text-secondary, #555);
  font-size: 1.1rem;
}

.profile-fields {
  width: 100%;
  margin-bottom: 20px; /* Aumentato leggermente per più spazio prima dei bottoni */
}

.profile-field {
  margin-bottom: 15px; /* Aumentato per leggibilità */
  font-size: 1rem; /* Leggermente ridotto per coerenza con altri testi */
  color: var(--text-secondary, #555);
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
}
.profile-field strong {
  color: var(--text-primary, #2c3e50);
  font-weight: 500;
  margin-right: 8px;
  min-width: 120px; 
  display: inline-block;
}
.profile-field span {
  word-break: break-word;
}

.action-buttons { /* Sostituisce .center-btns */
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px; /* Leggermente ridotto */
  margin: 25px 0 15px 0; /* Margini aggiornati */
  width: 100%;
}

.btn { /* Stile base per tutti i bottoni, poi specializzato */
  padding: 12px 25px;
  border: none;
  border-radius: var(--border-radius-md, 8px);
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: background-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  text-align: center;
  min-width: 140px;
}
.btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}
.btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: none;
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.modify-btn { /* Per Edit Profile / Cancel Edit */
  background-color: var(--primary-color, #f4b660);
  color: var(--bg-white, #ffffff);
}
.modify-btn:hover:not(:disabled) {
  background-color: var(--primary-hover-color, #e0a850);
}

.danger-btn { /* Per Logout */
  background-color: var(--danger-color, #e74c3c);
  color: var(--bg-white, #ffffff);
}
.danger-btn:hover:not(:disabled) {
  background-color: var(--danger-hover-color, #c0392b);
}

.save-btn { /* Per Save Residence / Change Password */
  background-color: var(--primary-color, #f4b660);
  color: var(--bg-white, #ffffff);
  width: 100%; /* Occupa tutta la larghezza nel form */
  margin-top: 10px; /* Spazio sopra il bottone nel form */
}
.save-btn:hover:not(:disabled) {
  background-color: var(--primary-hover-color, #e0a850);
}


.edit-form-section { /* Sostituisce .edit-form */
  margin-bottom: 20px; /* Spazio tra le sezioni del form */
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center; /* Centra il contenuto se necessario, ma con width 100% non dovrebbe servire */
}

.form-group {
  margin-bottom: 18px; /* Aumentato spazio */
  width: 100%;
}

.form-group label {
  display: block;
  margin-bottom: 8px; /* Aumentato spazio */
  font-weight: 500;
  color: var(--text-secondary, #555);
  font-size: 0.95rem; /* Leggermente più piccolo per le label */
}

input[type="text"], input[type="password"] {
  width: 100%;
  padding: 12px 15px; /* Padding aumentato */
  border: 1px solid var(--border-color, #cccccc); /* Bordo come da richiesta */
  border-radius: var(--border-radius-md, 8px); /* Raggio aggiornato */
  font-size: 1rem;
  font-family: 'Poppins', sans-serif; /* Applica il font */
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
input[type="text"]:focus, input[type="password"]:focus {
  outline: none;
  border-color: var(--primary-color, #f4b660);
  box-shadow: var(--input-focus-shadow, 0 0 0 3px rgba(244, 182, 96, 0.3));
}

.form-separator {
  margin: 30px 0; /* Aumentato spazio */
  border: none;
  border-top: 1px solid var(--border-color, #cccccc); /* Bordo più visibile */
  width: 100%;
}

/* Stili per i messaggi di successo ed errore */
.message {
  padding: 12px 15px;
  margin-top: 15px;
  border-radius: var(--border-radius-md, 8px);
  font-size: 0.95rem;
  text-align: center;
  border-width: 1px;
  border-style: solid;
}
.success-message {
  background-color: #e6f9f0; /* Sfondo verde chiaro */
  color: var(--success-text-color, #27ae60);
  border-color: var(--success-color, #2ecc71);
}
.error-message {
  background-color: #fdeded; /* Sfondo rosso chiaro */
  color: var(--error-text-color, #c0392b); 
  border-color: var(--danger-color, #e74c3c);
}
.main-error { /* Messaggio di errore principale nel box del profilo */
  margin-bottom: 20px; /* Spazio sotto se è il messaggio di errore principale */
}


/* Transizione per il pannello di modifica */
.slide-from-right-enter-active,
.slide-from-right-leave-active {
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.slide-from-right-enter-from,
.slide-from-right-leave-to {
  opacity: 0;
  transform: translateX(50px); /* Scorre da destra */
}
/* Rimuovo la vecchia transizione slide-fade se non più usata per il dropdown */
/*
.slide-fade-enter-active, .slide-fade-leave-active {
  transition: all 0.3s;
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(40px);
}
*/
</style>
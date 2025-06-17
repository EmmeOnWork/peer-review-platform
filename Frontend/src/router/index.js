import { createRouter, createWebHistory } from 'vue-router';
import LoginPage from '../views/LoginPage.vue';
import RegistrationPage from '../views/RegistrationPage.vue';
import TeacherDashboard from '../views/teacher/TeacherDashboard.vue';
import StudentDashboard from '../views/student/StudentDashboard.vue';
import NotFoundPage from '../views/NotFoundPage.vue';

// Mock per lo stato di autenticazione e ruolo
// In un'app reale, questo verrebbe da Pinia/Vuex o localStorage dopo il login
const isAuthenticated = () => !!localStorage.getItem('userToken');
const getUserRole = () => localStorage.getItem('userRole');

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginPage,
    meta: { requiresGuest: true } // Per reindirizzare se già loggato
  },
  {
    path: '/register',
    name: 'Register',
    component: RegistrationPage,
    meta: { requiresGuest: true } // Per reindirizzare se già loggato
  },
  {
    path: '/',
    redirect: () => { // Reindirizza alla dashboard appropriata o al login
      if (!isAuthenticated()) {
        return '/login';
      }
      const role = getUserRole();
      if (role === 'teacher') {
        return '/teacher/dashboard';
      } else if (role === 'student') {
        return '/student/dashboard';
      }
      return '/login'; // Fallback
    }
  },
  // --- Rotte Docente ---
  {
    path: '/teacher/dashboard',
    name: 'TeacherDashboard',
    component: TeacherDashboard,
    meta: { requiresAuth: true, role: 'teacher' }
  },
  // TODO: Aggiungere altre rotte per docenti (assignments, details, etc.)
  // { path: '/teacher/assignments', name: 'TeacherAssignments', component: () => import('../views/teacher/TeacherAssignmentsPage.vue'), meta: { requiresAuth: true, role: 'teacher' }},
   

  // --- Rotte Studente ---
  {
    path: '/student/dashboard',
    name: 'StudentDashboard',
    component: StudentDashboard,
    meta: { requiresAuth: true, role: 'student' }
  },
  // TODO: Aggiungere altre rotte per studenti (assignments, review, etc.)
  // { path: '/student/assignments', name: 'StudentAssignments', component: () => import('../views/student/StudentAssignmentsPage.vue'), meta: { requiresAuth: true, role: 'student' }},

  // --- Not Found ---
  {
    path: '/:pathMatch(.*)*', // Cattura tutte le rotte non definite
    name: 'NotFound',
    component: NotFoundPage
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

// Navigation Guard
router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresGuest = to.matched.some(record => record.meta.requiresGuest);
  const requiredRole = to.meta.role;

  if (requiresAuth && !isAuthenticated()) {
    next('/login'); // Se la rotta richiede auth ma l'utente non è loggato, vai al login
  } else if (requiresGuest && isAuthenticated()) {
    next('/'); // Se la rotta è per ospiti (login) ma l'utente è loggato, vai alla home
  } else if (requiresAuth && requiredRole && getUserRole() !== requiredRole) {
    // Se la rotta richiede un ruolo specifico e l'utente non ha quel ruolo
    // Potresti reindirizzare a una pagina di "accesso negato" o alla sua dashboard
    alert('Accesso non autorizzato per questo ruolo.');
    next(getUserRole() === 'teacher' ? '/teacher/dashboard' : '/student/dashboard');
  }
  else {
    next(); // Altrimenti, procedi
  }
});

export default router;
import { createRouter, createWebHistory } from 'vue-router';
import LoginPage from '../views/LoginPage.vue';
import RegistrationPage from '../views/RegistrationPage.vue';
import TeacherDashboard from '../views/teacher/TeacherDashboard.vue';
import StudentDashboard from '../views/student/StudentDashboard.vue';
import NotFoundPage from '../views/NotFoundPage.vue';
import UserProfile from '../components/auth/UserProfile.vue';

// Mock per lo stato di autenticazione e ruolo
const isAuthenticated = () => !!localStorage.getItem('userToken');
const getUserRole = () => localStorage.getItem('userRole');

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginPage,
    meta: { requiresGuest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: RegistrationPage,
    meta: { requiresGuest: true }
  },
  {
    path: '/',
    redirect: () => {
      if (!isAuthenticated()) {
        return '/login';
      }
      const role = getUserRole();
      if (role === 'teacher') {
        return '/teacher/dashboard';
      } else if (role === 'student') {
        return '/student/dashboard';
      }
      return '/login';
    }
  },
  {
    path: '/teacher/dashboard',
    name: 'TeacherDashboard',
    component: TeacherDashboard,
    meta: { requiresAuth: true, role: 'teacher' }
  },
  // ADD THIS ROUTE:
  {
    path: '/student/dashboard',
    name: 'StudentDashboard', 
    component: StudentDashboard,
    meta: { requiresAuth: true, role: 'student' }
  },

  // --- Rotte Docente ---
  {
    path: '/teacher/assignments',
    name: 'TeacherAssignments',
    component: () => import('../views/teacher/TeacherAssignmentsPage.vue'),
    meta: { requiresAuth: true, role: 'teacher' }
  },
  // Aggiungi queste due route:
  {
    path: '/teacher/assignments/:assignmentId/submissions',
    name: 'TeacherSubmissionsList',
    component: () => import('../views/teacher/SubmissionsListPage.vue'),
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/teacher/assignments/:assignmentId/submissions/:submissionId',
    name: 'TeacherSubmissionDetails',
    component: () => import('../views/teacher/SubmissionDetailsPage.vue'),
    meta: { requiresAuth: true, role: 'teacher' }
  },
  // NEW: Teacher Reports Route
  {
    path: '/teacher/reports',
    name: 'TeacherReports',
    component: () => import('../views/teacher/TeacherReportsPage.vue'),
    meta: { requiresAuth: true, role: 'teacher' }
  },
  
  // --- Rotte Studente ---
  {
    path: '/student/submissions',
    name: 'MySubmissions',
    component: () => import('../views/student/MySubmissionsPage.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },
  // NEW: Student Submission Reviews Route
  {
    path: '/student/submissions/:submissionId/reviews',
    name: 'SubmissionReviews',
    component: () => import('../views/student/SubmissionReviewsPage.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/student/assignments',
    name: 'StudentAssignments',
    component: () => import('../views/student/StudentAssignmentsPage.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/student/assignments/:assignmentId/submit',
    name: 'StudentSubmissionForm',
    component: () => import('../views/student/SubmissionFormPage.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },

  // Rotte per visualizzare le submissions degli studenti
  {
    path: '/student/submissions',
    name: 'MySubmissions',
    component: () => import('../views/student/MySubmissionsPage.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/student/submissions/:submissionId',
    name: 'StudentSubmissionDetails',
    component: () => import('../views/student/SubmissionDetailsPage.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },

  // --- Rotta Profilo Utente ---
  {
    path: '/profile',
    name: 'UserProfile',
    component: UserProfile,
    meta: { requiresAuth: true }
  },

  {
    path: '/student/reviews',
    name: 'StudentPeerReviews',
    component: () => import('../views/student/PeerReviewsPage.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/student/reviews/:reviewId',
    name: 'PeerReviewForm',
    component: () => import('../views/student/PeerReviewFormPage.vue'),
    meta: { requiresAuth: true, role: 'student' }
  },

  // --- Not Found ---
  {
    path: '/:pathMatch(.*)*',
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
    next('/login');
  } else if (requiresGuest && isAuthenticated()) {
    next('/');
  } else if (requiresAuth && requiredRole && getUserRole() !== requiredRole) {
    alert('Accesso non autorizzato per questo ruolo.');
    next(getUserRole() === 'teacher' ? '/teacher/dashboard' : '/student/dashboard');
  }
  else {
    next();
  }
});

export default router;

// src/store/index.js
import { createStore } from 'vuex';

export default createStore({
  state: {
    userToken: localStorage.getItem('userToken') || null,
    userRole: localStorage.getItem('userRole') || null,
    user: JSON.parse(localStorage.getItem('user')) || null, // Aggiungi questo
  },
  getters: {
    isAuthenticated: (state) => !!state.userToken,
    userRole: (state) => state.userRole,
    user: (state) => state.user, // Aggiungi questo
  },
  mutations: {
    SET_USER_TOKEN(state, token) {
      state.userToken = token;
      if (token) {
        localStorage.setItem('userToken', token);
      } else {
        localStorage.removeItem('userToken');
      }
    },
    SET_USER_ROLE(state, role) {
      state.userRole = role;
      if (role) {
        localStorage.setItem('userRole', role);
      } else {
        localStorage.removeItem('userRole');
      }
    },
    SET_USER(state, user) { // Aggiungi questa mutation
      state.user = user;
      if (user) {
        localStorage.setItem('user', JSON.stringify(user));
      } else {
        localStorage.removeItem('user');
      }
    },
    CLEAR_AUTH_DATA(state) {
      state.userToken = null;
      state.userRole = null;
      state.user = null; // Aggiungi questo
      localStorage.removeItem('userToken');
      localStorage.removeItem('userRole');
      localStorage.removeItem('user'); // Aggiungi questo
    }
  },
  actions: {
    logout({ commit }) {
      commit('CLEAR_AUTH_DATA');
    },
    // Aggiungi questa action per il login
    login({ commit }, { token, user }) {
      commit('SET_USER_TOKEN', token);
      commit('SET_USER_ROLE', user.role);
      commit('SET_USER', user);
    }
  },
  modules: {}
});
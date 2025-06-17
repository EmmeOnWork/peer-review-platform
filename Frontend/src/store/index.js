import { createStore } from 'vuex';

export default createStore({
  state: {
    userToken: localStorage.getItem('userToken') || null,
    userRole: localStorage.getItem('userRole') || null,
  },
  getters: {
    isAuthenticated: (state) => !!state.userToken,
    userRole: (state) => state.userRole,
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
    CLEAR_AUTH_DATA(state) {
      state.userToken = null;
      state.userRole = null;
      localStorage.removeItem('userToken');
      localStorage.removeItem('userRole');
    }
  },
  actions: {
    logout({ commit }) {
      commit('CLEAR_AUTH_DATA');
    }
    // Aggiungi altre actions se necessario, come il login
  },
  modules: {}
});
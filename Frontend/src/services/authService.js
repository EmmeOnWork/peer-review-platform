import axios from 'axios';

class AuthService {
  constructor() {
    this.baseURL = '/auth';
  }

  getAuthHeaders() {
    const token = localStorage.getItem('userToken');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  // Cerca studenti per nome e cognome usando l'endpoint che hai menzionato
  async searchStudentsByName(name = '', surname = '') {
    try {
      const params = new URLSearchParams();
      if (name) params.append('name', name);
      if (surname) params.append('surname', surname);
      
      const response = await axios.get(`${this.baseURL}/users/search?${params}`, {
        headers: this.getAuthHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Error searching students:', error);
      throw error;
    }
  }

  // Ottieni tutti gli studenti (come già usato in reviewService)
  async getAllStudents() {
    try {
      const response = await axios.get(`${this.baseURL}/users/students`, {
        headers: this.getAuthHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching all students:', error);
      throw error;
    }
  }

  // Metodo helper per ottenere dettagli studente per serial number
  async getStudentBySerialNumber(serialNumber) {
    try {
      const allStudents = await this.getAllStudents();
      return allStudents.find(student => student.serialNumber === serialNumber);
    } catch (error) {
      console.error('Error finding student by serial number:', error);
      return null;
    }
  }
}

export default new AuthService();
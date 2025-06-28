import axios from 'axios';

class ReportService {
  constructor() {
    this.baseURL = '/reports';
  }

  getAuthHeaders() {
    const token = localStorage.getItem('userToken');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  // Ottieni tutti i report del teacher
  async getTeacherReports(serialNumber) {
    try {
      const response = await axios.get(`${this.baseURL}/teacher/${serialNumber}`, {
        headers: this.getAuthHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching teacher reports:', error);
      throw error;
    }
  }

  // Ottieni le review per una submission specifica dello studente
  async getStudentSubmissionReviews(serialNumber, submissionId) {
    try {
      const response = await axios.get(`${this.baseURL}/student/${serialNumber}/submissions/${submissionId}`, {
        headers: this.getAuthHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching submission reviews:', error);
      throw error;
    }
  }
}

export default new ReportService();
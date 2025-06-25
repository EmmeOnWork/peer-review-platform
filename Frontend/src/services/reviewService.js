import axios from 'axios';

class ReviewService {
  constructor() {
    this.baseURL = '/reviews';
  }

  getAuthHeaders() {
    const token = localStorage.getItem('userToken');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  // Ottenere tutti gli studenti di un assignment
  async getAssignmentStudents(assignmentId) {
    // Ottieni i serial number degli studenti dall'assignment
    const assignmentStudentsResponse = await axios.get(`/assignments/${assignmentId}/students`, {
      headers: this.getAuthHeaders()
    });
    const studentSerialNumbers = assignmentStudentsResponse.data;
    
    // Ottieni tutti i dettagli degli studenti
    const studentsResponse = await axios.get(`/auth/users/students`, {
      headers: this.getAuthHeaders()
    });
    const allStudents = studentsResponse.data;
    
    // Filtra solo gli studenti che sono nell'assignment
    return allStudents.filter(student => 
      studentSerialNumbers.includes(student.serialNumber)
    );
  }

  async assignAutoReview(assignmentId, minReviews) {
    try {
      const response = await axios.post(`${this.baseURL}/assign/auto`, {
        assignmentId,
        minReviews
      }, {
        headers: this.getAuthHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Error in auto assignment:', error);
      throw error;
    }
  }

  async assignManualReview(assignmentId, manualAssignments) {
    try {
      const response = await axios.post(`${this.baseURL}/assign/manual`, {
        assignmentId,
        manualAssignments
      }, {
        headers: this.getAuthHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Error in manual assignment:', error);
      throw error;
    }
  }

  // Ottenere le peer review assegnate a uno studente
  async getStudentPeerReviews(studentSerialNumber) {
    try {
      const response = await axios.get(`${this.baseURL}/student/${studentSerialNumber}`, {
        headers: this.getAuthHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching student peer reviews:', error);
      throw error;
    }
  }

  // Metodo per ottenere i dettagli di una submission per peer review
  async getSubmissionForReview(submissionId) {
    const response = await axios.get(`/submissions/for-review/${submissionId}`, {
      headers: this.getAuthHeaders()
    });
    return response.data;
  }

  // Metodo per scaricare un allegato di una submission in peer review
  async downloadSubmissionAttachment(submissionId, filename) {
    const response = await axios.get(`/submissions/for-review/${submissionId}/download/${filename}`, {
      headers: this.getAuthHeaders(),
      responseType: 'blob'
    });
    return response;
  }

  // Inviare una peer review
  async submitPeerReview(reviewId, evaluation) {
    try {
      const response = await axios.put(`${this.baseURL}/${reviewId}`, {
        evaluation
      }, {
        headers: this.getAuthHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Error submitting peer review:', error);
      throw error;
    }
  }

  // Ottenere i dettagli di una specifica peer review
  async getPeerReviewById(reviewId) {
    try {
      const response = await axios.get(`${this.baseURL}/${reviewId}`, {
        headers: this.getAuthHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching peer review details:', error);
      throw error;
    }
  }
}

// Esporta un'istanza della classe
export default new ReviewService();
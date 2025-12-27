const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Helper function for API calls
const apiCall = async (endpoint, options = {}) => {
  const url = `${API_URL}${endpoint}`;
  const token = localStorage.getItem('token');

  const headers = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || 'Request failed');
  }

  return response.json();
};

// User APIs
export const registerUser = async (userData) => {
  return apiCall('/users/register', {
    method: 'POST',
    body: JSON.stringify(userData),
  });
};

export const loginUser = async (credentials) => {
  return apiCall('/users/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  });
};

export const getUser = async (userId) => {
  return apiCall(`/users/${userId}`);
};

// Quiz APIs
export const createQuiz = async (userId, quizData) => {
  return apiCall(`/quiz/create?user_id=${userId}`, {
    method: 'POST',
    body: JSON.stringify(quizData),
  });
};

export const getUserQuizzes = async (userId) => {
  return apiCall(`/quiz/user/${userId}`);
};

export const getAssignedQuizzes = async (userId) => {
  return apiCall(`/quiz/assigned/${userId}`);
};

export const getQuiz = async (quizId) => {
  return apiCall(`/quiz/${quizId}`);
};

export const getQuizWithAnswers = async (quizId) => {
  return apiCall(`/quiz/${quizId}/with-answers`);
};

export const assignQuiz = async (assignedBy, assignmentData) => {
  return apiCall(`/quiz/assign?assigned_by=${assignedBy}`, {
    method: 'POST',
    body: JSON.stringify(assignmentData),
  });
};

// Test APIs
export const startTest = async (userId, testData) => {
  return apiCall(`/test/start?user_id=${userId}`, {
    method: 'POST',
    body: JSON.stringify(testData),
  });
};

export const submitTest = async (submissionData) => {
  return apiCall('/test/submit', {
    method: 'POST',
    body: JSON.stringify(submissionData),
  });
};

export const getTestResult = async (uqtId) => {
  return apiCall(`/test/result/${uqtId}`);
};

export const getUserTests = async (userId) => {
  return apiCall(`/test/user/${userId}`);
};

export const getPendingTests = async (userId) => {
  return apiCall(`/test/user/${userId}/pending`);
};

export const getCompletedTests = async (userId) => {
  return apiCall(`/test/user/${userId}/completed`);
};

export const getTestSummary = async (userId) => {
  return apiCall(`/test/summary/${userId}`);
};


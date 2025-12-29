import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// User Authentication
export const registerUser = async (userData) => {
  const response = await api.post('/users/register', userData);
  return response.data;
};

export const loginUser = async (username, password) => {
  const response = await api.post('/users/login', {
    username,
    password
  });
  return response.data;
};

export const getUser = async (userId) => {
  const response = await api.get(`/users/${userId}`);
  return response.data;
};

// Quiz Management
export const createQuiz = async (userId, quizData) => {
  const response = await api.post(`/quiz/create?user_id=${userId}`, quizData);
  return response.data;
};

export const getUserQuizzes = async (userId) => {
  const response = await api.get(`/quiz/user/${userId}`);
  return response.data;
};

export const getAssignedQuizzes = async (userId) => {
  const response = await api.get(`/quiz/assigned/${userId}`);
  return response.data;
};

export const getQuiz = async (quizId) => {
  const response = await api.get(`/quiz/${quizId}`);
  return response.data;
};

export const assignQuiz = async (teacherId, assignmentData) => {
  const response = await api.post(`/quiz/assign?assigned_by=${teacherId}`, assignmentData);
  return response.data;
};

// Test Management
export const startTest = async (userId, quizId, assignmentId = null) => {
  // Convert assignmentId to integer or null
  const assignmentIdInt = assignmentId ? parseInt(assignmentId, 10) : null;
  
  const response = await api.post(
    `/test/start?user_id=${userId}`,
    {
      quiz_id: parseInt(quizId, 10),
      quiz_assignment_id: assignmentIdInt
    }
  );
  return response.data;
};

export const submitTest = async (testData) => {
  const response = await api.post('/test/submit', testData);
  return response.data;
};

export const getTestResult = async (uqtId) => {
  const response = await api.get(`/test/result/${uqtId}`);
  return response.data;
};

export const getUserTests = async (userId) => {
  const response = await api.get(`/test/user/${userId}`);
  return response.data;
};

export const getPendingTests = async (userId) => {
  const response = await api.get(`/test/user/${userId}/pending`);
  return response.data;
};

export const getCompletedTests = async (userId) => {
  const response = await api.get(`/test/user/${userId}/completed`);
  return response.data;
};

export const getTestSummary = async (userId) => {
  const response = await api.get(`/test/summary/${userId}`);
  return response.data;
};

export default api;


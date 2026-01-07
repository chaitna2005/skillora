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

export const getUserStats = async (userId) => {
  const response = await api.get(`/users/${userId}/stats`);
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

export const getQuiz = async (quizId, forTest = false, uqtId = null) => {
  const params = new URLSearchParams();
  if (forTest) {
    params.append('for_test', 'true');
    if (uqtId) {
      params.append('uqt_id', uqtId.toString());
    }
  }
  const queryString = params.toString();
  const url = `/quiz/${quizId}${queryString ? `?${queryString}` : ''}`;
  const response = await api.get(url);
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

export const getTestResult = async (userId, quizId) => {
  const response = await api.get(`/test/result?user_id=${userId}&quiz_id=${quizId}`);
  return response.data;
};

export const getTestAnswers = async (uqtId) => {
  const response = await api.get(`/test/answers/${uqtId}`);
  return response.data;
};

export const saveAnswer = async (uqtId, questionId, optionIds) => {
  const response = await api.post(`/test/save-answer/${uqtId}`, {
    question_id: questionId,
    question_option_ids: optionIds
  });
  return response.data;
};

export const getHint = async (questionId, questionText, options) => {
  const response = await api.post(`/test/hint/${questionId}`, {
    question_text: questionText,
    options: options
  });
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

export const deletePendingTest = async (userId, uqtId) => {
  const response = await api.delete(`/test/pending/${uqtId}?user_id=${userId}`);
  return response.data;
};

export const deleteQuiz = async (userId, quizId) => {
  const response = await api.delete(`/quiz/${quizId}?user_id=${userId}`);
  return response.data;
};

// Bulk delete APIs
export const deleteAllPendingTests = async (userId) => {
  const response = await api.delete(`/test/pending/all?user_id=${userId}`);
  return response.data;
};

export const deleteAllCompletedTests = async (userId) => {
  const response = await api.delete(`/test/completed/all?user_id=${userId}`);
  return response.data;
};

export const deleteAllUserQuizzes = async (userId) => {
  const response = await api.delete(`/quiz/user/${userId}/all`);
  return response.data;
};

export const deleteAllAssignedQuizzes = async (userId) => {
  const response = await api.delete(`/quiz/assigned/${userId}/all`);
  return response.data;
};

// Bulk delete with IDs APIs
export const bulkDeletePendingTests = async (userId, ids) => {
  const response = await api.post(`/test/pending/bulk-delete?user_id=${userId}`, { ids });
  return response.data;
};

export const bulkDeleteCompletedTests = async (userId, ids) => {
  const response = await api.post(`/test/completed/bulk-delete?user_id=${userId}`, { ids });
  return response.data;
};

export const bulkDeleteQuizzes = async (userId, ids) => {
  const response = await api.post(`/quiz/bulk-delete?user_id=${userId}`, { ids });
  return response.data;
};

export const bulkDeleteAssignedQuizzes = async (userId, ids) => {
  const response = await api.post(`/quiz/assigned/bulk-delete?user_id=${userId}`, { ids });
  return response.data;
};

// Example Prompts
export const getExamplePrompts = async (userId) => {
  const response = await api.get('/prompts/examples', {
    params: { user_id: userId }
  });
  return response.data;
};

export const trackPromptUsage = async (promptId) => {
  const response = await api.post(`/prompts/${promptId}/use`);
  return response.data;
};

// Quiz Assignment & Sharing
export const createShareLink = async (quizId, teacherId) => {
  const response = await api.post(`/quiz/${quizId}/assign?teacher_id=${teacherId}`);
  return response.data;
};

export const getAssignmentInfo = async (token) => {
  const response = await api.get(`/assignments/${token}`);
  return response.data;
};

export const claimAssignment = async (shareToken, userId) => {
  const response = await api.post(`/assignments/${shareToken}/claim?user_id=${userId}`);
  return response.data;
};

export const getAssignmentResults = async (teacherId) => {
  const response = await api.get(`/quiz/assign/results/${teacherId}`);
  return response.data;
};

export const getQuizAnalytics = async (teacherId) => {
  const response = await api.get(`/quiz/assign/analytics/${teacherId}`);
  return response.data;
};

export const getQuestionDifficulty = async (quizId, teacherId) => {
  const response = await api.get(`/quiz/${quizId}/question-difficulty/${teacherId}`);
  return response.data;
};

export const exportQuizResultsCSV = async (teacherId, quizId = null) => {
  const url = quizId 
    ? `/quiz/export/results/${teacherId}?quiz_id=${quizId}`
    : `/quiz/export/results/${teacherId}`;
  const response = await api.get(url, {
    responseType: 'blob'
  });
  return response.data;
};

export default api;


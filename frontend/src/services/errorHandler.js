/**
 * Extract error message from API error response
 * Handles various error formats from the backend
 */
export const getErrorMessage = (error, defaultMessage = 'An error occurred') => {
  // If error has a response from the server
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail;
    
    // If detail is a string, use it directly
    if (typeof detail === 'string') {
      return detail;
    }
    
    // If detail is an array (validation errors), extract messages
    if (Array.isArray(detail)) {
      return detail.map(e => {
        if (typeof e === 'string') return e;
        if (e.msg) return e.msg;
        if (e.message) return e.message;
        return JSON.stringify(e);
      }).join('; ');
    }
    
    // If detail is an object, try to get message
    if (typeof detail === 'object') {
      return detail.msg || detail.message || defaultMessage;
    }
  }
  
  // Check for error message
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  
  // Check for error string
  if (error.message) {
    return error.message;
  }
  
  return defaultMessage;
};

export default getErrorMessage;


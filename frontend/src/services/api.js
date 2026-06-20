import axios from "axios";

const api = axios.create({
  baseURL: "https://pdf-reader-backend-4rea.onrender.com",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const authService = {
  register: (data) => api.post("/auth/register", data),
  login: (data) => api.post("/auth/login", data),
  forgotPassword: (email) => api.post("/auth/forgot-password", { email }),
  resetPassword: (token, newPassword) => api.post("/auth/reset-password", { token, new_password: newPassword }),
  me: () => api.get("/auth/me"),
  changePassword: (currentPassword, newPassword) => api.post("/auth/change-password", { current_password: currentPassword, new_password: newPassword }),
};

export const documentService = {
  getFileUrl: (documentId) => `${api.defaults.baseURL}/documents/${documentId}/file`,
  upload: (file) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/documents/upload", form);
  },
  getMyDocuments: () => api.get("/documents/me"),
  deleteDocument: (id) => api.delete(`/documents/${id}`),
};

export const analysisService = {
  exportPdf: (documentId) => api.get(`/analysis/${documentId}/export`, { responseType: "blob" }),
  run: (documentId) => api.post(`/analysis/run/${documentId}`),
  get: (documentId) => api.get(`/analysis/${documentId}`),
};

export default api;

export const notesService = {
  create: (documentId, content, pageNumber = null) => api.post(`/notes/${documentId}`, { content, page_number: pageNumber }),
  getByDocument: (documentId) => api.get(`/notes/${documentId}`),
  delete: (noteId) => api.delete(`/notes/${noteId}`),
};

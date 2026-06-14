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
  me: () => api.get("/auth/me"),
};

export const documentService = {
  upload: (file) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/documents/upload", form);
  },
  getMyDocuments: () => api.get("/documents/me"),
  deleteDocument: (id) => api.delete(`/documents/${id}`),
};

export const analysisService = {
  run: (documentId) => api.post(`/analysis/run/${documentId}`),
  get: (documentId) => api.get(`/analysis/${documentId}`),
};

export default api;

async function request(path, options = {}) {
  const response = await fetch(path, { credentials: 'same-origin', ...options });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `请求失败 (${response.status})`);
  return data;
}

const json = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

export const api = {
  me: () => request('/api/auth/me/'),
  login: (payload) => request('/api/auth/login/', json('POST', payload)),
  register: (payload) => request('/api/auth/register/', json('POST', payload)),
  logout: () => request('/api/auth/logout/', { method: 'POST' }),
  projects: () => request('/api/projects/'),
  createProject: (payload) => request('/api/projects/', json('POST', payload)),
  profile: () => request('/api/profile/'),
  updateProfile: (payload) => request('/api/profile/', json('PATCH', payload)),
  preferences: () => request('/api/preferences/'),
  updatePreferences: (payload) => request('/api/preferences/', json('PATCH', payload)),
  uploadSource: (projectId, file) => {
    const body = new FormData();
    body.append('project_id', projectId);
    body.append('file', file);
    return request('/api/uploads/', { method: 'POST', body });
  },
  createDiagnosisJob: (sourceId, context = {}) => request('/api/diagnosis-jobs/', json('POST', { source_id: sourceId, context })),
  diagnosisConfig: () => request('/api/diagnosis-config/'),
  diagnosisJobs: (projectId) => request(`/api/diagnosis-jobs/${projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''}`),
  diagnosisJob: (jobId) => request(`/api/diagnosis-jobs/${jobId}/`),
  diagnoses: (projectId) => request(`/api/diagnoses/${projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''}`),
  saveDiagnosis: (payload) => request('/api/diagnoses/', json('POST', payload)),
};

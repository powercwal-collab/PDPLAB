const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS', 'TRACE']);

function cookie(name) {
  return document.cookie
    .split(';')
    .map(value => value.trim())
    .find(value => value.startsWith(`${name}=`))
    ?.slice(name.length + 1);
}

async function ensureCsrfToken() {
  let token = cookie('csrftoken');
  if (!token) {
    await fetch('/api/auth/csrf/', { credentials: 'same-origin' });
    token = cookie('csrftoken');
  }
  return token ? decodeURIComponent(token) : '';
}

async function request(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const headers = new Headers(options.headers || {});
  if (!SAFE_METHODS.has(method)) {
    const token = await ensureCsrfToken();
    if (token) headers.set('X-CSRFToken', token);
  }
  const response = await fetch(path, { credentials: 'same-origin', ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const fallback = response.status === 401
      ? '登录状态已失效，请重新登录'
      : response.status === 403
        ? '安全校验失败，请刷新页面后重试'
        : `请求失败 (${response.status})`;
    throw new Error(data.error || fallback);
  }
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
  deleteDiagnosis: (diagnosisId) => request(`/api/diagnoses/${diagnosisId}/`, { method: 'DELETE' }),
};

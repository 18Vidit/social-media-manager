/**
 * Pulse — API Client
 * Handles all communication with the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API error ${res.status}: ${errorText}`);
  }
  
  return res.json();
}

// ── Brand APIs ──
export const api = {
  // Health
  health: () => fetchAPI('/health'),
  
  // Seed
  seed: () => fetchAPI('/api/seed', { method: 'POST' }),
  
  // Brands
  getBrands: () => fetchAPI('/api/brands'),
  getBrand: (id: string) => fetchAPI(`/api/brands/${id}`),
  createBrand: (data: any) => fetchAPI('/api/brands', { method: 'POST', body: JSON.stringify(data) }),
  getGuidelines: (brandId: string) => fetchAPI(`/api/brands/${brandId}/guidelines`),
  ingestPosts: (brandId: string, posts: any[]) => fetchAPI(`/api/brands/${brandId}/ingest`, {
    method: 'POST',
    body: JSON.stringify({ brand_id: brandId, posts }),
  }),
  
  // Content Generation
  generateContent: (data: any) => fetchAPI('/api/content/generate', { method: 'POST', body: JSON.stringify(data) }),
  getDrafts: (brandId?: string, status?: string) => {
    const params = new URLSearchParams();
    if (brandId) params.set('brand_id', brandId);
    if (status) params.set('status', status);
    return fetchAPI(`/api/content/drafts?${params}`);
  },
  approveDraft: (draftId: string, scheduledTime?: string) => fetchAPI(`/api/content/drafts/${draftId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ scheduled_time: scheduledTime }),
  }),
  rejectDraft: (draftId: string, reason: string) => fetchAPI(`/api/content/drafts/${draftId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  }),
  
  // Schedule
  getPeakTimes: (platform?: string) => fetchAPI(`/api/schedule/peak-times?platform=${platform || 'instagram'}`),
  getUpcoming: (brandId?: string) => fetchAPI(`/api/schedule/upcoming${brandId ? `?brand_id=${brandId}` : ''}`),
  
  // Comments
  getComments: (brandId?: string) => fetchAPI(`/api/comments${brandId ? `?brand_id=${brandId}` : ''}`),
  getTriageView: (brandId?: string) => fetchAPI(`/api/comments/triage${brandId ? `?brand_id=${brandId}` : ''}`),
  checkCircuitBreaker: (brandId?: string) => fetchAPI(`/api/comments/circuit-breaker${brandId ? `?brand_id=${brandId}` : ''}`),
  
  // Analytics
  getDashboard: (brandId?: string) => fetchAPI(`/api/analytics/dashboard${brandId ? `?brand_id=${brandId}` : ''}`),
  getPostAnalytics: (brandId?: string) => fetchAPI(`/api/analytics/posts${brandId ? `?brand_id=${brandId}` : ''}`),
  getAudience: () => fetchAPI('/api/analytics/audience'),
  getHeatmap: () => fetchAPI('/api/analytics/engagement-heatmap'),
  
  // Trends
  getTrends: (platform?: string) => fetchAPI(`/api/trends?platform=${platform || 'instagram'}`),
};

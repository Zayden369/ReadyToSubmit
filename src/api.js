const base = import.meta.env.VITE_REVIEW_API_URL?.replace(/\/$/, '');
let session;

export const isLiveApi = () => Boolean(base);

async function request(path, options = {}) {
  const response = await fetch(base + path, {
    ...options,
    headers: {
      'content-type': 'application/json',
      ...(session ? {'x-review-token': session.reviewToken} : {}),
      ...(options.headers || {}),
    },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || 'The review service is unavailable.');
  return data;
}

export async function uploadAndExtract(type, file) {
  if (!session) session = await request('/reviews', {method: 'POST'});
  const ticket = await request(`/reviews/${session.reviewId}/upload-url`, {
    method: 'POST',
    body: JSON.stringify({type, filename: file.name, contentType: file.type, size: file.size}),
  });
  const uploaded = await fetch(ticket.uploadUrl, {
    method: 'PUT',
    headers: {'content-type': file.type, 'x-amz-server-side-encryption': 'AES256'},
    body: file,
  });
  if (!uploaded.ok) throw new Error('Private upload failed. Please try again.');
  return request(`/reviews/${session.reviewId}/documents/${type}/process`, {
    method: 'POST',
    body: JSON.stringify({key: ticket.key, filename: file.name, contentType: file.type}),
  });
}

export async function getLiveReview() {
  if (!session) throw new Error('Start a review first.');
  return request(`/reviews/${session.reviewId}`);
}

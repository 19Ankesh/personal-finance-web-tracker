import client from './client'

export const uploadCSV = (file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return client.post('/upload/csv', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress
      ? (e) => onProgress(Math.round((e.loaded * 100) / e.total))
      : undefined,
  }).then(r => r.data)
}

export const uploadPDF = (file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return client.post('/upload/pdf', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress
      ? (e) => onProgress(Math.round((e.loaded * 100) / e.total))
      : undefined,
  }).then(r => r.data)
}

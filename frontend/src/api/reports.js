import axios from './axios'

export const reportsApi = {
  // Get all reports
  getReports() {
    return axios.get('/reports/')
  },

  // Get a specific report
  getReport(id) {
    return axios.get(`/reports/${id}/`)
  },

  // Create a new report
  createReport(reportData) {
    return axios.post('/reports/', reportData)
  },

  // Update a report
  updateReport(id, reportData) {
    return axios.put(`/reports/${id}/`, reportData)
  },

  // Delete a report
  deleteReport(id) {
    return axios.delete(`/reports/${id}/`)
  },

  // Get report data for widgets
  getReportData(id) {
    return axios.get(`/reports/${id}/data/`)
  },

  // Get aggregated data for charts
  getAggregatedData(params) {
    return axios.get('/reports/data/aggregated/', { params })
  }
}

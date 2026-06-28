import BaseApi from "./baseApi";

class ApiClient extends BaseApi {

  constructor() {
    super();
  }

  async login(email: string, password: string) {

    const formData = new URLSearchParams();

    formData.append("username", email);
    formData.append("password", password);

    const response = await this.client.post(
      "/auth/login",
      formData,
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      }
    );

    const token = response.data.access_token;

    this.setToken(token);

    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  async forgotPassword(email: string) {
    const response = await this.client.post('/auth/forgot-password', { email });
    return response.data;
  }

  async resetPassword(
    token: string,
    newPassword: string
  ) {

    const response =
      await this.client.post(
        "/auth/reset-password",
        {
          token,
          new_password: newPassword
        }
      );

    return response.data;
  }

  async changePassword(
    oldPassword: string,
    newPassword: string
  ) {

    const response =
      await this.client.post(
        "/auth/change-password",
        {
          old_password: oldPassword,
          new_password: newPassword
        }
      );

    return response.data;
  }

  async adminResetPassword(
    userId: number,
    newPassword: string
  ) {

    const response =
      await this.client.post(
        `/auth/admin-reset-password/${userId}`,
        {
          new_password: newPassword
        }
      );

    return response.data;
  }

  async getUsers() {

    const response =
      await this.client.get(
        "/users"
      );

    return response.data;
  }

  async getUsersForMembership() {

    const response =
      await this.client.get(
        "/users/available-for-membership"
      );

    return response.data;
  }

  async getUser(id: number) {
    const response = await this.client.get(`/users/${id}`);
    return response.data;
  }

  async createUser(data: {
    name: string;
    email: string;
    password: string;
    role: string;
  }) {

    const response =
      await this.client.post(
        '/users',
        data
      );

    return response.data;
  }

  async activateUser(userId: number) {
    const response =
      await this.client.patch(
        `/users/${userId}/activate`
      );

    return response.data;
  }

  async deactivateUser(userId: number) {
    const response =
      await this.client.patch(
        `/users/${userId}/deactivate`
      );

    return response.data;
  }

  async getUsersByRole(role: string) {
    const response =
      await this.client.get(
        `/users/role/${role}`
      );

    return response.data;
  }

  async getClubs() {

    const response =
      await this.client.get(
        "/clubs"
      );

    return response.data;
  }

  async getClub(id: number) {
    const response = await this.client.get(`/clubs/${id}`);
    return response.data;
  }

  async createClub(
    data: {
      club_name: string;
      description?: string;
    }
  ) {

    const response =
      await this.client.post(
        "/clubs",
        data
      );

    return response.data;
  }

  async getMyClubs() {

    const response =
      await this.client.get(
        "/clubs/my-clubs"
      );

    return response.data;
  }

  async getClubEvents(
    clubId: number
  ) {

    const response =
      await this.client.get(
        `/clubs/${clubId}/events`
      );

    return response.data;
  }

  async getClubStats(
    clubId: number
  ) {

    const response =
      await this.client.get(
        `/clubs/${clubId}/stats`
      );

    return response.data;
  }

  async getClubMembers(clubId: number) {

    const response =
      await this.client.get(
        `/club-memberships/club/${clubId}`
      );

    return response.data;
  }

  async getMemberships() {
    const response = await this.client.get(
      '/club-memberships'
    );
    return response.data;
  }

  async createMembership(data: {
    user_id: number;
    club_id: number;
    role: string;
  }) {
    const response =
      await this.client.post(
        '/club-memberships',
        data
      );

    return response.data;
  }

  async bulkAssignMembership(data: {
    user_id: number;
    club_ids: number[];
    role: string;
  }) {

    const response =
      await this.client.post(
        "/club-memberships/bulk-assign",
        data
      );

    return response.data;
  }

  async getMyMemberships() {

    const response =
      await this.client.get(
        "/club-memberships/my-memberships"
      );

    return response.data;
  }

  async getEvents() {

    const response =
      await this.client.get(
        "/events"
      );

    return response.data;
  }

  async getEvent(id: number) {
    const response = await this.client.get(`/events/${id}`);
    return response.data;
  }

  async createEvent(
    data: {
      club_id: number;
      event_title: string;
      event_category?: string;
      event_date?: string;
    }
  ) {

    const response =
      await this.client.post(
        "/events",
        data
      );

    return response.data;
  }

  async getEventCategories() {

    const response =
      await this.client.get(
        "/events/categories"
      );

    return response.data;
  }

  async getMyEvents() {

    const response =
      await this.client.get(
        "/events/my-events"
      );

    return response.data;
  }

  async getEventsByClub(
    clubId: number
  ) {

    const response =
      await this.client.get(
        `/events/club/${clubId}`
      );

    return response.data;
  }

  async getEventStats(
    eventId: number
  ) {

    const response =
      await this.client.get(
        `/events/${eventId}/stats`
      );

    return response.data;
  }

  async getReports(
    skip = 0,
    limit = 20
  ) {

    const response =
      await this.client.get(
        "/reports",
        {
          params: {
            skip,
            limit
          }
        }
      );

    return response.data;
  }

  async getReport(id: number) {
    const response = await this.client.get(`/reports/${id}`);
    return response.data;
  }

  async submitReport(data: {eventId: string; file: File;}) {
    const formData = new FormData();
    formData.append("event_id",data.eventId);
    formData.append("file",data.file);
    const response = await this.client.post("/reports/submit",formData);
    return response.data;
  }

  async resubmitReport(
    reportId: number,
    file: File
  ) {

    const formData =
      new FormData();

    formData.append(
      "report_id",
      String(reportId)
    );

    formData.append(
      "file",
      file
    );

    const response =
      await this.client.post(
        "/reports/resubmit",
        formData
      );

    return response.data;
  }

  async getReportStatus(
    reportId: number
  ) {

    const response =
      await this.client.get(
        `/reports/${reportId}/status`
      );

    return response.data;
  }

  async getReportSummary(
    reportId: number
  ) {

    const response =
      await this.client.get(
        `/reports/${reportId}/summary`
      );

    return response.data;
  }

  async getReportHistory(
    reportId: number
  ) {

    const response =
      await this.client.get(
        `/reports/${reportId}/history`
      );

    return response.data;
  }

  async getReportVersions(
    reportId: number
  ) {

    const response =
      await this.client.get(
        `/reports/${reportId}/versions`
      );

    return response.data;
  }

  async getMyReports() {
    const response = await this.client.get("/reports/my-reports");
    return response.data;
  }

  async getReportCompliance(reportId: number) {
    const response = await this.client.get(`/reports/${reportId}/compliance`);
    return response.data;
  }

  async getReportFeedback(reportId: number) {
    const response = await this.client.get(`/reports/${reportId}/feedback`);
    return response.data;
  }

  async getTemplates() {
    const response = await this.client.get('/templates');
    return response.data;
  }

  async getActiveTemplate() {
    const response = await this.client.get('/templates/current');
    return response.data;
  }

  async uploadTemplate(version: string, file: File) {

    const formData = new FormData();

    formData.append("file",file);

    const response = await this.client.post(
      "/templates/upload",
      formData,
      { params: { version } }
    );

    return response.data;
  }

  async getRepositoryRecords() {
    const response = await this.client.get("/repository/events");
    return response.data;
  }

  async getRepositoryRecord(id: number) {
    const response = await this.client.get(`/repository/event/${id}`);
    return response.data;
  }

  async getNotifications() {

    const response =
      await this.client.get(
        "/notifications"
      );

    return response.data;
  }

  async markNotificationRead(id: number) {
    const response = await this.client.patch(`/notifications/${id}/read`);
    return response.data;
  }

  async markAllNotificationsRead() {
    const response = await this.client.patch("/notifications/read-all");
    return response.data;
  }

  async getLatestNotifications() {

    const response =
      await this.client.get(
        "/notifications/latest"
      );

    return response.data;
  }

  async getUnreadNotificationCount() {

    const response =
      await this.client.get(
        "/notifications/unread-count"
      );

    return response.data;
  }

  async getNotificationStats() {

    const response =
      await this.client.get(
        "/notifications/stats"
      );

    return response.data;
  }

  async getPendingReviews() {
    const response = await this.client.get("/reviews/pending");
    return response.data;
  }

  async approveReview(reportId: number, comments: string) {
    const response = await this.client.post("/reviews/approve",
        {
          report_id: reportId,
          comments
        }
      );
    return response.data;
  }

  async requestRevision(reportId: number, comments: string) {

    const response = await this.client.post("/reviews/revision-required",
        {
          report_id: reportId,
          comments
        }
      );
    return response.data;
  }

  async getReviews() {
    const response =
      await this.client.get(
        "/reviews"
      );

    return response.data;
  }

  async getReviewStats() {
    const response =
      await this.client.get(
        "/reviews/stats"
      );

    return response.data;
  }

  async getReviewReportDetails(
    reportId: number
  ) {
    const response =
      await this.client.get(
        `/reviews/report/${reportId}`
      );

    return response.data;
  }

  async getReportLatestReview(
    reportId: number
  ) {

    const response =
      await this.client.get(
        `/reports/${reportId}/latest-review`
      );

    return response.data;
  }

  async getReportTemplateStatus(
    reportId: number
  ) {

    const response =
      await this.client.get(
        `/reports/${reportId}/template-status`
      );

    return response.data;
  }

  async getReviewHistory(
    reportId: number
  ) {
    const response =
      await this.client.get(
        `/reviews/report/${reportId}/history`
      );

    return response.data;
  }

  async getLatestReview(
    reportId: number
  ) {
    const response =
      await this.client.get(
        `/reviews/report/${reportId}/latest`
      );

    return response.data;
  }

  async getReportEmailDraft(
    reportId: number
  ) {

    const response =
      await this.client.get(
        `/reports/${reportId}/email-draft`
      );

    return response.data;
  }

  async getRecentNotifications() {
    const response =
      await this.client.get(
        "/dashboard/recent-notifications"
      );

    return response.data;
  }

  async getRecentReports() {
    const response =
      await this.client.get(
        "/dashboard/recent-reports"
      );

    return response.data;
  }

  async getStudentDashboard() {
    const response =
      await this.client.get(
        "/dashboard/student"
      );

    return response.data;
  }

  async getStudentReportStatus() {
    const response =
      await this.client.get(
        "/dashboard/student/status"
      );

    return response.data;
  }

  async getCoordinatorDashboard() {
    const response =
      await this.client.get(
        "/dashboard/coordinator"
      );

    return response.data;
  }

  async getFacultyDashboard() {
    const response =
      await this.client.get(
        "/dashboard/faculty"
      );

    return response.data;
  }

  async getAdminDashboard() {
    const response =
      await this.client.get(
        "/dashboard/admin"
      );

    return response.data;
  }

  async getAdminReportSummary() {
    const response =
      await this.client.get(
        "/dashboard/admin/report-summary"
      );

    return response.data;
  }

  async getClubPerformance() {
    const response =
      await this.client.get(
        "/dashboard/admin/club-performance"
      );

    return response.data;
  }

  async getAdminRepositoryStats() {
    const response =
      await this.client.get(
        "/dashboard/admin/repository-stats"
      );

    return response.data;
  }

  async generateFeedback(
    validationResultId: number
  ) {

    const response =
      await this.client.post(
        `/feedback/generate/${validationResultId}`
      );

    return response.data;
  }

  async generateFeedbackBundle(
    validationResultId: number
  ) {

    const response =
      await this.client.post(
        `/feedback/${validationResultId}`
      );

    return response.data;
  }

  async searchRepository(
    query?: string,
    category?: string,
    venue?: string
  ) {
    const response =
      await this.client.get(
        "/repository/search",
        {
          params: {
            query,
            category,
            venue
          }
        }
      );

    return response.data;
  }

  async getRepositoryStats() {
    const response =
      await this.client.get(
        "/repository/stats"
      );

    return response.data;
  }

  async getClubRepositoryRecords(
    clubId: number
  ) {
    const response =
      await this.client.get(
        `/repository/club/${clubId}`
      );

    return response.data;
  }

  async getCategoryRepositoryRecords(
    category: string
  ) {
    const response =
      await this.client.get(
        `/repository/event-category/${category}`
      );

    return response.data;
  }

  async createTemplate(
    data: {
      version: string;
      template_schema: any;
    }
  ) {

    const response =
      await this.client.post(
        "/templates",
        data
      );

    return response.data;
  }

  async analyzeTemplate(
    version: string,
    file: File
  ) {

    const formData =
      new FormData();

    formData.append(
      "file",
      file
    );

    const response =
      await this.client.post(
        "/templates/analyze",
        formData,
        { params: { version } }
      );

    return response.data;
  }

  async getTemplateImpactAnalysis() {

    const response =
      await this.client.get(
        "/templates/impact-analysis"
      );

    return response.data;
  }

}

export const api = new ApiClient();
export default api;

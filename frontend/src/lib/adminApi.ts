import BaseApi from "./baseApi";

class AdminApi extends BaseApi {

  constructor() {
    super();
  }

  async parsePdf(path: string) {

    const response =
      await this.client.get(
        "/parser/pdf",
        {
          params: { path }
        }
      );

    return response.data;
  }

  async parseDocx(path: string) {

    const response =
      await this.client.get(
        "/parser/docx",
        {
          params: { path }
        }
      );

    return response.data;
  }

  async extractPdf(path: string) {

    const response =
      await this.client.get(
        "/parser/extract-pdf",
        {
          params: { path }
        }
      );

    return response.data;
  }

  async validatePdf(path: string) {

    const response =
      await this.client.get(
        "/parser/validate-pdf",
        {
          params: { path }
        }
      );

    return response.data;
  }

  async validateReportVersion(
    filename: string,
    reportVersionId: number
  ) {

    const response =
      await this.client.post(
        "/compliance/validate",
        null,
        {
          params: {
            filename,
            report_version_id:
              reportVersionId
          }
        }
      );

    return response.data;
  }

  async initializeDriveRepository() {

    const response =
      await this.client.post(
        "/drive/initialize-repository"
      );

    return response.data;
  }

  async testDriveUpload() {

    const response =
      await this.client.post(
        "/drive/test"
      );

    return response.data;
  }

  async getSystemHealth() {

    const response =
      await this.client.get(
        "/system/health"
      );

    return response.data;
  }

  async getSystemStats() {

    const response =
      await this.client.get(
        "/system/stats"
      );

    return response.data;
  }

    async uploadFile(
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
        "/upload",
        formData
      );

    return response.data;
  }
  
}

export const adminApi =
  new AdminApi();

export default adminApi;
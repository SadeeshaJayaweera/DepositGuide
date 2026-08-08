export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async healthCheck() {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.json();
  }
}

export const apiClient = new ApiClient();

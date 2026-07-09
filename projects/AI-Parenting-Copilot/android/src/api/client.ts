// 创建/修改该文件的LLM大模型：Arena.ai Agent Mode
// 创建时间（北京时间）：2026-07-09 11:10:00


export type ApiClientConfig = {
  baseUrl: string;
  token?: string;
};

export type ApiResponse<T> = {
  status: number;
  data: T;
};

export class ApiClient {
  private config: ApiClientConfig;

  constructor(config: ApiClientConfig) {
    this.config = { ...config, baseUrl: config.baseUrl.replace(/\/$/, '') };
  }

  get baseUrl(): string {
    return this.config.baseUrl;
  }

  setToken(token: string | undefined): void {
    this.config.token = token;
  }

  headers(): Record<string, string> {
    const headers: Record<string, string> = { 'content-type': 'application/json' };
    if (this.config.token) {
      headers.authorization = `Bearer ${this.config.token}`;
    }
    return headers;
  }

  async healthz(): Promise<ApiResponse<{ status: string }>> {
    const response = await fetch(`${this.config.baseUrl}/healthz`, { headers: this.headers() });
    return { status: response.status, data: await response.json() };
  }

  async post<T>(path: string, body: unknown): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.config.baseUrl}${path}`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(body),
    });
    return { status: response.status, data: await response.json() };
  }
}

export const defaultApiClient = new ApiClient({
  baseUrl: process.env.PARENTING_API_BASE_URL ?? 'http://127.0.0.1:8000',
});

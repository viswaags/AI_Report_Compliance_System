import axios, {
  AxiosInstance,
  AxiosError,
  InternalAxiosRequestConfig
} from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  "http://localhost:8000";

class BaseApi {

  protected client: AxiosInstance;

  private token: string | null = null;

  constructor() {

    this.client = axios.create({
      baseURL: API_BASE_URL
    });

    const storedToken =
      localStorage.getItem("token");

    if (storedToken) {
      this.token = storedToken;
    }

    this.client.interceptors.request.use(
      (
        config: InternalAxiosRequestConfig
      ) => {

        if (this.token) {

          config.headers.Authorization =
            `Bearer ${this.token}`;
        }

        return config;
      }
    );

    this.client.interceptors.response.use(

      (response) => response,

      (error: AxiosError) => {

        if (
          error.response?.status === 401
        ) {

          this.clearToken();

          localStorage.removeItem(
            "user"
          );

          window.dispatchEvent(
            new Event("auth:expired")
          );

          if (
            window.location.pathname !==
            "/auth/login"
          ) {
            window.history.replaceState(
              null,
              "",
              "/auth/login"
            );
          }
        }

        return Promise.reject(error);
      }
    );
  }

  setToken(token: string) {

    this.token = token;

    localStorage.setItem(
      "token",
      token
    );
  }

  clearToken() {

    this.token = null;

    localStorage.removeItem(
      "token"
    );

    localStorage.removeItem(
      "user"
    );
  }

  getToken() {

    return this.token;
  }
}

export default BaseApi;

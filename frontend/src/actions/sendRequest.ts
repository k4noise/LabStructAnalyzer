import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from "axios";

/**
 * Represents the data from successful request
 * @template T data type
 * @property {T | null} data data
 * @property {number | null} error error HTTP status code
 */
interface ResponseData<T> {
  data: T | null;
  error: number | null;
  description: string | null;
}

/**
 * An enumeration of HTTP methods that can be used with the `sendRequest` function
 */
enum AxiosMethod {
  GET = "get",
  POST = "post",
  PUT = "put",
  PATCH = "patch",
  DELETE = "delete",
  HEAD = "head",
  OPTIONS = "options",
}

/**
 * Sends an HTTP request to the specified URL using the specified method and options
 * @template ResType data return type
 * @param {string} url url
 * @param {AxiosMethod} method HTTP method, look at enum
 * @param {boolean} needAuth flag need use withCredentials or not
 * @param {Object} [body] request payload
 * @returns {Promise<ResponseData<ResponseType>>}
 */
const sendRequest = async <ResponseType>(
  url: string,
  method: AxiosMethod,
  needAuth: boolean,
  body?: object
): Promise<ResponseData<ResponseType>> => {
  let data: ResponseType | null = null;
  let error: number | null = null;
  let description: string | null = null;

  const config: AxiosRequestConfig = {
    validateStatus(status) {
      return status >= 200 && status < 303;
    },
  };

  if (needAuth) {
    config.withCredentials = true;
  }

  try {
    let response: AxiosResponse<ResponseType>;
    if (method === "get") {
      response = await axios[method](url, config);
    } else {
      response = await axios[method](url, body, config);
    }

    data = response.data;
  } catch (err) {
    if (axios.isAxiosError(err)) {
      const axiosError: AxiosError = err;
      error = Number(axiosError.response?.status ?? 500);
      const responseData = axiosError.response?.data;
      description =
        responseData["detail"] ||
        responseData["message"] ||
        `"${JSON.stringify(responseData)}"`;

      if (error === 401 && needAuth) {
        const { error: updateError } = await sendRequest<void>(
          "/api/v1/jwt/refresh",
          AxiosMethod.POST,
          true
        );
        if (updateError) {
          await sendRequest<void>(  
            "/api/v1/jwt/logout",
            AxiosMethod.DELETE,
            true
          );
          return { data: null, error: 401, description: "Не авторизован" };
        }

        if (method === "get") {
          const retryResponse = await axios[method](url, config);
          data = retryResponse.data;
          error = null;
          description = null;
        } else {
          const retryResponse = await axios[method](url, body, config);
          data = retryResponse.data;
          error = null;
          description = null;
        }
      }
    }
  }

  return { data, error, description };
};

export { sendRequest, AxiosMethod };

import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { NavigateFunction } from 'react-router';
import Cookies from 'js-cookie';

/**
 * An array of HTTP status codes that indicate an error page should be displayed
 */
const ERROR_PAGES = [401, 403, 404];

/**
 * Represents the data from successful request
 * @template T data type
 * @property {T | null} data data
 * @property {number | null} error error HTTP status code
 */
interface ResponseData<T> {
  data: T | null;
  error: number | null;
}

/**
 * An enumeration of HTTP methods that can be used with the `sendRequest` function
 */
enum AxiosMethod {
  GET = 'get',
  POST = 'post',
  PUT = 'put',
  PATCH = 'patch',
  DELETE = 'delete',
  HEAD = 'head',
  OPTIONS = 'options',
}

/**
 * Sends an HTTP request to the specified URL using the specified method and options
 * @template ResType data return type
 * @param {string} url url
 * @param {AxiosMethod} method HTTP method, look at enum
 * @param {boolean} needAuth flag need use withCredintals or not
 * @param {Object} [body] request payload
 * @returns {Promise<ResponseData<ResType>>}
 */
const sendRequest = async <ResType>(
  url: string,
  method: AxiosMethod,
  needAuth: boolean,
  body?: object
): Promise<ResponseData<ResType>> => {
  let data: ResType | null = null;
  let error: number | null = null;

  try {
    let response;
    const config: AxiosRequestConfig = {
      validateStatus(status) {
        return status >= 200 && status < 303;
      },
    };
    if (needAuth) {
      const accessToken = Cookies.get('csrf_access_token');
      if (accessToken) {
      config.headers = {
        ...(config.headers || {}),
        "X-CSRF-Token": accessToken,
      };
      }
      config.withCredentials = true;
    }

    if (method === 'get') response = await axios[method](url, config);
    else response = await axios[method](url, body, config);
    data = response.data;
  } catch (err) {
    if (axios.isAxiosError(err)) {
      const axiosError: AxiosError = err;
      console.error(axiosError);
      error = Number(axiosError.response?.status ?? 500);
    }
  }

  return { data, error };
};

/**
 * Handles errors by redirecting to specific error pages.
 * @param {number} error HTTP status code [4xx]
 * @param {NavigateFunction} navigate react callback to redirect
 */
const handleError = (error: number, navigate: NavigateFunction) => {
  if (ERROR_PAGES.includes(error)) {
    navigate(`/${error}`);
  }
};

export { sendRequest, handleError, AxiosMethod };
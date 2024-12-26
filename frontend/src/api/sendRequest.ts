import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from "axios";

/**
 * Представляет данные успешного или неудачного запроса.
 *
 * @template T Тип данных ответа.
 * @property {T | null} data Данные ответа (если запрос успешен).
 * @property {number | null} error HTTP-код ошибки (если запрос завершился с ошибкой).
 * @property {string | null} description Описание ошибки или дополнительные детали.
 */
interface ResponseData<T> {
  data: T | null;
  error: number | null;
  description: string | null;
}

/**
 * Перечисление HTTP-методов, которые можно использовать в функции `sendRequest`.
 *
 * @enum {string}
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
 * Отправляет HTTP-запрос на указанный URL с заданным методом и параметрами.
 *
 * @template ResponseType Тип возвращаемых данных.
 * @param {string} url URL-адрес, на который отправляется запрос.
 * @param {AxiosMethod} method HTTP-метод запроса (GET, POST и т.д.).
 * @param {boolean} needAuth Флаг, указывающий, требуется ли авторизация (используется `withCredentials`).
 * @param {Object} [body] Тело запроса (для методов POST, PUT и т.д.).
 * @returns {Promise<ResponseData<ResponseType>>} Промис с 3 свойствами - данные, код ошибки и описание ошибки
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

      // Попытка обновления токена при ошибке 401
      if (error === 401 && needAuth) {
        try {
          await axios.post("/api/v1/jwt/refresh", null, config);
        } catch (error) {
          await axios.delete("/api/v1/jwt/logout", config);
          return { data: null, error: 401, description: "Не авторизован" };
        }

        // Повторный запрос после обновления токена
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

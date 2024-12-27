import axios, { AxiosResponse } from "axios";

/**
 * Создает экземпляр axios с настроенными параметрами.
 *
 * @returns {axios.AxiosInstance} Экземпляр axios с настроенными параметрами.
 */
const api = axios.create({
  withCredentials: true,
  validateStatus(status) {
    return status >= 200 && status < 303;
  },
});

/**
 * Обрабатывает успешные и ошибочные ответы от сервера.
 *
 * @param {AxiosResponse} response - Успешный ответ от сервера.
 * @returns {AxiosResponse} Успешный ответ.
 *
 * @param {Error} error - Ошибка, возвращенная сервером.
 * @returns {Promise<AxiosResponse | never>} Обещание, которое разрешается с успешным ответом или отклоняется с ошибкой.
 */
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        // Использование axios вместо api - не ошибка, тут работа перехватчиков лишняя
        await axios.post("/api/v1/jwt/refresh/", { withCredentials: true });
        return await api(originalRequest);
      } catch (refreshError) {
        await axios.delete("/api/v1/jwt/logout/", { withCredentials: true });
        window.location.href = "/";
      }
    }
    throw error;
  }
);

/**
 * Извлекает сообщение из ответа сервера.
 *
 * @param {AxiosResponse} response - Ответ от сервера.
 * @returns {string} Сообщение из ответа сервера.
 */
const extractMessage = (response: AxiosResponse) => {
  const body = response.data;
  const data = getMessageInDefaultFields(body) || body;

  if (!Array.isArray(data)) {
    return data;
  }

  const messageParts = [];
  for (const dataPart of data) {
    messageParts.push(getMessageInDefaultFields(dataPart));
  }

  return messageParts.join("\n") || body;
};

/**
 * Извлекает сообщение из стандартных полей ответа.
 *
 * @param {any} body - Тело ответа.
 * @returns {string | undefined} Сообщение из полей `detail`, `message` или `msg` тела ответа.
 */
const getMessageInDefaultFields = (body) => {
  return body.detail || body.message || body.msg;
};

export { api, extractMessage };

import { AxiosMethod, sendRequest } from "./sendRequest";

/**
 * Получает название текущего курса.
 * @async
 * @returns {Promise<{ name: string } | undefined>} Объект, содержащий название курса (`name`), или `undefined` в случае ошибки.
 */
export const getCourseName = async () => {
  const data = await sendRequest<{ name: string }>(
    "/api/v1/courses/current",
    AxiosMethod.GET,
    true
  );
  return data;
};

import { CourseInfo } from "./dto/course";
import { AxiosMethod, sendRequest } from "./sendRequest";

/**
 * Получает название текущего курса.
 * @async
 * @returns {Promise<CourseInfo | undefined>} Объект, содержащий название курса (`name`), или `undefined` в случае ошибки.
 */
export const getCourseName = async () => {
  const data = await sendRequest<CourseInfo>(
    "/api/v1/courses/current",
    AxiosMethod.GET,
    true
  );
  return data;
};

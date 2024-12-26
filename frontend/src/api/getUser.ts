import { UserCourseInfo } from "./dto/user";
import { AxiosMethod, sendRequest } from "./sendRequest";
/**
 * Получает информацию о текущем пользователе.
 *
 * @async
 * @returns {Promise<UserCourseInfo>} Объект с информацией о пользователе.
 */
export const getUser = async () => {
  const data = await sendRequest<UserCourseInfo>(
    "/api/v1/users/me",
    AxiosMethod.GET,
    true
  );
  return data;
};
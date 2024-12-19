import { UserCourseInfo } from "./dto/user";
import { AxiosMethod, sendRequest } from "./sendRequest";

export const getUser = async () => {
  const data = await sendRequest<UserCourseInfo>(
    "/api/v1/users/me",
    AxiosMethod.GET,
    true
  );
  return data;
};

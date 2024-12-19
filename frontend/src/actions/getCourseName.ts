import { AxiosMethod, sendRequest } from "./sendRequest";

export const getCourseName = async () => {
  const data = await sendRequest<{ name: string }>(
    "/api/v1/courses/current",
    AxiosMethod.GET,
    true
  );
  return data;
};

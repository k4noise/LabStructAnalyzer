import { AxiosMethod, sendRequest } from "./sendRequest";

export const sendTemplate = async (formData: FormData) => {
  const data = await sendRequest<object[]>("/api/template", AxiosMethod.POST, true, formData);
  return data;
}
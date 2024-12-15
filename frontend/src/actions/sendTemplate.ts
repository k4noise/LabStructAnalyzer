import { TemplateElement } from "./dto/template";
import { AxiosMethod, sendRequest } from "./sendRequest";

export const sendTemplate = async (formData: FormData) => {
  const data = await sendRequest<TemplateElement[]>("/api/v1/template", AxiosMethod.POST, true, formData);
  return data;
}
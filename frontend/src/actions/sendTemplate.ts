import { TemplateElement } from "./dto/template";
import { AxiosMethod, sendRequest } from "./sendRequest";

/**
 * Отправляет шаблон на сервер с помощью запроса POST
 *
 * @async
 * @function
 * @param {FormData} formData - Данные формы, содержащие информацию для отправки.
 * @returns {Promise<TemplateElement[]>} Промис, который разрешается массивом элементов шаблона.
 */
export const sendTemplate = async (formData: FormData) => {
  const data = await sendRequest<TemplateElement[]>(
    "/api/v1/template",
    AxiosMethod.POST,
    true,
    formData
  );
  return data;
};

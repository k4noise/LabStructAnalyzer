import { AxiosMethod, sendRequest } from "./sendRequest";

/**
 * Отправляет шаблон на сервер с помощью запроса POST
 *
 * @async
 * @function
 * @param {FormData} formData - Данные формы, содержащие информацию для отправки.
 * @returns {Promise<TemplateElement[]>} Промис, который разрешается идентификатором загруженного шаблона.
 */
export const sendTemplate = async (formData: FormData) => {
  const data = await sendRequest<{ template_id: string }>(
    "/api/v1/template",
    AxiosMethod.POST,
    true,
    formData
  );
  return data;
};

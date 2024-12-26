import { TemplateModel } from "./dto/template";
import { AxiosMethod, sendRequest } from "./sendRequest";

/**
 * Получает шаблон с сервера с помощью запроса GET
 *
 * @async
 * @function
 * @param {string} id - Идентификатор шаблона.
 * @returns {Promise<TemplateModel>} Промис, который разрешается элементом шаблона.
 */
export const getTemplate = async (id: string) => {
  const data = await sendRequest<TemplateModel>(
    `/api/v1/template/${id}`,
    AxiosMethod.GET,
    true
  );
  return data;
};

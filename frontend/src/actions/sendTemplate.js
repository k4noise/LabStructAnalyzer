import { AxiosMethod, sendRequest } from "./sendRequest";
export const sendTemplate = async (formData) => {
    const data = await sendRequest("/api/template", AxiosMethod.POST, true, formData);
    return data;
};

import axios from 'axios';
/**
 * An array of HTTP status codes that indicate an error page should be displayed
 */
const ERROR_PAGES = [401, 403, 404];
/**
 * An enumeration of HTTP methods that can be used with the `sendRequest` function
 */
var AxiosMethod;
(function (AxiosMethod) {
    AxiosMethod["GET"] = "get";
    AxiosMethod["POST"] = "post";
    AxiosMethod["PUT"] = "put";
    AxiosMethod["PATCH"] = "patch";
    AxiosMethod["DELETE"] = "delete";
    AxiosMethod["HEAD"] = "head";
    AxiosMethod["OPTIONS"] = "options";
})(AxiosMethod || (AxiosMethod = {}));
/**
 * Sends an HTTP request to the specified URL using the specified method and options
 * @template ResType data return type
 * @param {string} url url
 * @param {AxiosMethod} method HTTP method, look at enum
 * @param {boolean} needAuth flag need use withCredintals or not
 * @param {Object} [body] request payload
 * @returns {Promise<ResponseData<ResType>>}
 */
const sendRequest = async (url, method, needAuth, body) => {
    let data = null;
    let error = null;
    try {
        let response;
        const config = {
            validateStatus(status) {
                return status >= 200 && status < 303;
            },
        };
        if (needAuth) {
            config.withCredentials = true;
        }
        if (method === 'get')
            response = await axios[method](url, config);
        else
            response = await axios[method](url, body, config);
        data = response.data;
    }
    catch (err) {
        if (axios.isAxiosError(err)) {
            const axiosError = err;
            console.error(axiosError);
            error = Number(axiosError.response?.status ?? 500);
        }
    }
    return { data, error };
};
/**
 * Handles errors by redirecting to specific error pages.
 * @param {number} error HTTP status code [4xx]
 * @param {NavigateFunction} navigate react callback to redirect
 */
const handleError = (error, navigate) => {
    if (ERROR_PAGES.includes(error)) {
        navigate(`/${error}`);
    }
};
export { sendRequest, handleError, AxiosMethod };

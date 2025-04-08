import { useRouteError } from "react-router";
import BackButtonComponent from "../../components/BackButtonComponent";
import { AxiosError } from "axios";
import { extractMessage } from "../../utils/sendRequest";
import { Helmet } from "react-helmet";

/**
 * Компонент для отображения страницы ошибок.
 * Обрабатывает ошибки AxiosError и некоторые дефолтные.
 */
const ErrorPage = () => {
  const error = useRouteError() as Error;

  /**
   * Представляет ошибку как 2 компоненты: код (для сетевой ошибки) и сообщение.
   * Сообщение может быть как текстовым, так и формата JSON.
   */
  const getErrorContent = () => {
    if (!error) {
      return { code: 404, message: "Не найдено" };
    }
    if (error instanceof AxiosError) {
      return {
        code: error.response?.status || error.status,
        message: extractMessage(error.response),
      };
    }
    return { message: error?.message };
  };

  const { code, message } = getErrorContent();

  return (
    <>
      <Helmet>
        <title>Ошибка</title>
      </Helmet>
      <BackButtonComponent positionClasses="mt-5" />
      <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        {!!code && <h1 className="text-8xl mb-8">{code}</h1>}
        {typeof message === "string" ? (
          <p className="leading-tight text-5xl text-center">{message}</p>
        ) : (
          <pre data-testid="json" className="leading-tight">
            {JSON.stringify(message, null, 2)}
          </pre>
        )}
      </div>
    </>
  );
};

export default ErrorPage;

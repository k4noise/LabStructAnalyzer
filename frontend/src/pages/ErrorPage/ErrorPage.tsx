import { useRouteError } from "react-router";
import BackButtonComponent from "../../components/BackButtonComponent";

/**
 * Компонент для отображения страницы ошибок.
 * Ошибка по умолчанию 404 Не найдено.
 */
const ErrorPage = () => {
  const error: Error = useRouteError() as Error;

  const DEFAULT_ERROR_CODE = 404;
  const DEFAULT_ERROR_MESSAGE = "Не найдено";

  let parsedError: { status: number; message: string } | null = null;

  if (error?.message) {
    try {
      parsedError = JSON.parse(error.message);
    } catch {
      parsedError = null;
    }
  }

  const errorCode = parsedError?.status ?? DEFAULT_ERROR_CODE;
  const definition =
    parsedError?.message && parsedError.message !== ""
      ? parsedError.message
      : DEFAULT_ERROR_MESSAGE;

  return (
    <>
      <BackButtonComponent positionClasses="mt-5" />
      <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        <h1 className="text-8xl mb-8">{errorCode}</h1>
        <p className="text-5xl">{definition}</p>
      </div>
    </>
  );
};

export default ErrorPage;

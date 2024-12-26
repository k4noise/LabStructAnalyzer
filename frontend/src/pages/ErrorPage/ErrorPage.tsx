import { useRouteError } from "react-router";
import BackButtonComponent from "../../components/BackButtonComponent";

/**
 * Компонент для отображения страницы ошибок.
 * Ошибка по умолчанию 404 Не найдено.
 * Для передачи кастомной ошибки используйте парамтеры URL - code и description.
 * Описание можно передавать как обычным сообщением, так и строкой JSON.
 * Строку с JSON обязательно заключите в двойные ("") кавычки
 *
 * @component
 * @returns {JSX.Element} - Рендерит страницу ошибок
 */
const ErrorPage = () => {
  const error: Error = useRouteError() as Error;

  let parsedError: { status: number; message: string };
  if (error) {
    parsedError = JSON.parse(error.message);
  }

  const DEFAULT_ERROR_CODE = 404;
  const DEFAULT_ERROR_MESSAGE = "Не найдено";

  const errorCode = parsedError?.status ?? DEFAULT_ERROR_CODE;

  let definition =
    errorCode === DEFAULT_ERROR_CODE
      ? DEFAULT_ERROR_MESSAGE
      : JSON.stringify(parsedError.message);

  if (!definition) {
    definition = DEFAULT_ERROR_MESSAGE;
  }

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

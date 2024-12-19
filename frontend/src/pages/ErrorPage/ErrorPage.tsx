import { useNavigate, useSearchParams } from "react-router";

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
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const DEFAULT_ERROR_CODE = 404;
  const DEFAULT_ERROR_MESSAGE = "Не найдено";

  const errorCode = searchParams.get("code") ?? DEFAULT_ERROR_CODE;

  let definition =
    errorCode === DEFAULT_ERROR_CODE
      ? DEFAULT_ERROR_MESSAGE
      : searchParams.get("description");

  if (definition && definition.startsWith('"') && definition.endsWith('"')) {
    try {
      definition = JSON.parse(definition.substring(1, definition.length - 1));
    } catch (err) {
      console.error("Ошибка при парсинге описания:", err);
    }
  }

  if (!definition) {
    definition = DEFAULT_ERROR_MESSAGE;
  }

  const handleGoBack = () => {
    navigate(-1, { replace: true });
  };

  return (
    <>
      <button
        className="absolute mt-5 ml-16 cursor-pointer"
        onClick={handleGoBack}
      >
        Назад
      </button>
      <div className="absolute top-1/3 left-1/3 -translate-y-1/3 -translate-x-1/3">
        <h1 className="text-8xl mb-8">{errorCode}</h1>
        <p className="text-5xl">{definition}</p>
      </div>
    </>
  );
};

export default ErrorPage;

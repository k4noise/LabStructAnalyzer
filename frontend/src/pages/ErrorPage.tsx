import { useSearchParams } from "react-router";

const DEFAULT_ERROR_CODE = 404;
const DEFAULT_ERROR_MESSAGE = "Не найдено";

const ErrorPage = () => {
  const [searchParams] = useSearchParams();
  const errorCode = searchParams.get("code") ?? DEFAULT_ERROR_CODE;
  let definition =
    errorCode == DEFAULT_ERROR_CODE
      ? DEFAULT_ERROR_MESSAGE
      : searchParams.get("description");
  if (definition.startsWith('"')) {
    const definitionNoQuot = definition.substring(1, definition.length - 1);
    try {
      definition = JSON.parse(definitionNoQuot);
    } catch (err) {
      definition = definitionNoQuot;
    }
  }
  return (
    <div className="absolute top-1/3 left-1/3 -translate-y-1/3 -translate-x-1/3">
      <h1 className="text-8xl mb-8">{errorCode}</h1>
      <p className="text-5xl">{definition}</p>
    </div>
  );
};

export default ErrorPage;

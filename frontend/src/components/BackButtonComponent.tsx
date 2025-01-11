import { useNavigate } from "react-router";

const BackButtonComponent = ({ positionClasses }) => {
  const navigate = useNavigate();

  const handleGoBack = () => {
    if (window.history.length > 1) navigate(-1);
    else navigate("/templates");
  };

  return (
    <button
      className={`absolute ${positionClasses} cursor-pointer underline`}
      onClick={handleGoBack}
      type="button"
    >
      Назад
    </button>
  );
};

export default BackButtonComponent;

import { useNavigate } from "react-router";

const BackButtonComponent = ({ positionClasses }) => {
  const navigate = useNavigate();

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <button
      className={`absolute ${positionClasses} cursor-pointer underline`}
      onClick={handleGoBack}
    >
      Назад
    </button>
  );
};

export default BackButtonComponent;

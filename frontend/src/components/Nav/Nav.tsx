import { useEffect, useState } from "react";
import { getUser } from "../../actions/getUser";
import { useNavigate } from "react-router";
import { UserCourseInfo } from "../../actions/dto/user";

/**
 * Компонент навигационной панели, отображающий информацию о пользователе.
 *
 * @component
 * @returns {JSX.Element} Элемент навигационной панели.
 */
const Nav = () => {
  /**
   * Хук навигации для перемещения между страницами
   * @type {Function}
   */
  const navigate = useNavigate();

  /**
   * Состояние, хранящее информацию о пользователе.
   * @type {UserCourseInfo | null}
   */
  const [userData, setUserData] = useState<UserCourseInfo | null>(null);

  /**
   * Асинхронная функция для получения данных пользователя.
   * Если данные уже загружены, функция завершает выполнение.
   * В случае ошибки перенаправляет на страницу ошибки.
   *
   * @async
   * @returns {void}
   */
  const getUserData = async () => {
    if (userData) {
      return;
    }

    const { data, error, description } = await getUser();

    if (error) {
      navigate(`/error?code=${error}&description=${description}`);
      return;
    }

    setUserData(data);
  };

  /**
   * Эффект, вызывающий загрузку данных пользователя при монтировании компонента.
   */
  useEffect(() => {
    getUserData();
  }, []);

  return (
    <nav className="min-h-20 flex  items-center justify-end gap-4">
      {userData?.avatarUrl && (
        <img
          className="w-10 h-10 rounded-full object-cover"
          src={userData.avatarUrl}
          alt="avatar"
        />
      )}
      {userData?.fullName && (
        <span>
          {userData.role.includes("student")
            ? `${userData.name} ${userData.surname}`
            : userData.fullName}
        </span>
      )}
    </nav>
  );
};

export default Nav;

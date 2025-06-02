import { useEffect } from "react";
import { useLoaderData } from "react-router";
import { UserCourseInfo } from "../../model/user";
import { api } from "../../utils/sendRequest";

/**
 * Компонент навигационной панели, отображающий информацию о пользователе.
 *
 * @component
 * @returns {JSX.Element} Элемент навигационной панели.
 */
const Nav = () => {
  const { data: userData } = useLoaderData<{ data: UserCourseInfo }>();

  // удивительной красоты костыль для того, чтобы бэкенд на render.com не ушел в спячку, пока у пользователя запущен фронтенд
  useEffect(() => {
    const pingServer = async () => {
      try {
        await api.get("/api");
        // действительно, нам тут все равно на возможную ошибку
      } catch (error) {}
    };

    const intervalId = setInterval(pingServer, 45000); // 45 сек

    return () => clearInterval(intervalId);
  }, []);

  return (
    <nav className="min-h-12 flex items-center justify-end gap-4">
      {userData?.avatarUrl && (
        <img
          className="w-10 h-10 rounded-full object-cover border-2 border-zinc-400"
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

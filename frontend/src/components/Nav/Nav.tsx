import { useLoaderData } from "react-router";
import { UserCourseInfo } from "../../model/user";

/**
 * Компонент навигационной панели, отображающий информацию о пользователе.
 *
 * @component
 * @returns {JSX.Element} Элемент навигационной панели.
 */
const Nav = () => {
  const { data: userData } = useLoaderData<{ data: UserCourseInfo }>();

  return (
    <nav className="min-h-12 flex  items-center justify-end gap-4">
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

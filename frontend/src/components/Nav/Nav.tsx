import { useEffect, useState } from "react";
import { getUser } from "../../actions/getUser";
import { useNavigate } from "react-router";
import { UserCourseInfo } from "../../actions/dto/user";

const Nav = () => {
  /**
   * Хук навигации для перемещения между страницами
   * @type {Function}
   */
  const navigate = useNavigate();

  const [userData, setUserData] = useState<UserCourseInfo | null>(null);

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
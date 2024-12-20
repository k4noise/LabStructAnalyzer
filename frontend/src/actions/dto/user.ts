/**
 * Интерфейс, представляющий информацию о пользователе курса.
 * @interface UserCourseInfo
 */
export interface UserCourseInfo {
  /**
   * Полное имя пользователя.
   * @type {string}
   */
  fullName: string;
  /**
   * Имя пользователя.
   * @type {string}
   */
  name: string;
  /**
   * Фамилия пользователя.
   * @type {string}
   */
  surname: string;
  /**
   * Роли пользователя (например, "student", "teacher", "assistant").
   * @type {Array<string>}
   */
  role: Array<string>;
  /**
   * URL аватара пользователя.
   * @type {string}
   */
  avatarUrl: string;
}

/**
 * Генерирует Tailwind CSS класс отступа слева на основе уровня вложенности.
 *
 * @param {number} [level=0] - Уровень вложенности.
 */
export const getMarginLeftStyle = (level: number = 0): string =>
  level ? `ml-${level * 4}` : "";

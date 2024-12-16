/**
 * Генерирует Tailwind CSS класс отступа слева на основе уровня вложенности.
 *
 * @param {number} [level=1] - Уровень вложенности.
 */
export const getMarginLeftStyle = (level: number = 1): string =>
  `ml-${level * 4}`;

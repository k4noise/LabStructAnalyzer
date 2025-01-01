import { ImageElement } from "../../model/template";

/**
 * Свойства для компонента ImageComponent.
 *
 * @interface ImageComponentProps
 * @property {ImageElement} element - Элемент изображения.
 */
interface ImageComponentProps {
  element: ImageElement;
}

/**
 * Компонент для отображения изображения.
 *
 * @param {ImageComponentProps} props - Свойства компонента.
 */
const ImageComponent: React.FC<ImageComponentProps> = ({ element }) => (
  <img src={element.properties.data} className="mx-auto" />
);

export default ImageComponent;

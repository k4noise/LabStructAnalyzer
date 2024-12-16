import { ImageElement } from "../../actions/dto/template";

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
  <img src={element.data} alt="" className="mx-auto" />
);

export default ImageComponent;

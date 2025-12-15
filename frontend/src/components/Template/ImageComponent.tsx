import { ImageElement } from "../../model/templateElement";

interface ImageComponentProps {
  element: ImageElement;
  level: number;
  children: any[];
  renderChild: (child: any) => React.ReactNode;
}

const ImageComponent: React.FC<ImageComponentProps> = ({ element }) => (
  <img
    src={`/${element.properties.data}`}
    className="mx-auto dark:brightness-75"
  />
);

export default ImageComponent;

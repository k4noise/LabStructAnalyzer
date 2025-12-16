import { ImageElement } from "../../model/templateElement";

interface ImageComponentProps {
  element: ImageElement;
}

const ImageComponent: React.FC<ImageComponentProps> = ({ element }) => (
  <div className="w-full my-6">
    <img
      src={`/${element.properties.data}`}
      className="mx-auto block max-w-full h-auto dark:brightness-75"
      alt="Template content"
    />
  </div>
);

export default ImageComponent;

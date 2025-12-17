import { HeaderElement } from "../../model/templateElement";
import { getMarginLeftStyle } from "../../utils/templateStyle";

const HeaderComponent: React.FC<{ element: HeaderElement }> = ({ element }) => {
  const { headerLevel, nestingLevel, data, numberingBulletText } =
    element.properties;
  const Tag = `h${headerLevel}` as keyof JSX.IntrinsicElements;

  const sizeMap: Record<number, string> = {
    1: "text-3xl my-8 font-bold",
    2: "text-2xl my-6 font-bold",
    3: "text-xl my-4 font-bold",
    4: "text-lg my-2 font-bold",
  };

  return (
    <Tag
      className={`${
        sizeMap[headerLevel] || "text-base font-bold"
      } ${getMarginLeftStyle(nestingLevel)} text-zinc-900 dark:text-zinc-50`}
    >
      {numberingBulletText ? `${numberingBulletText} ${data}` : data}
    </Tag>
  );
};

export default HeaderComponent;

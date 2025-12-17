import React from "react";

const TextComponent: React.FC<{ element: any }> = ({ element }) => {
  const { data, numberingBulletText } = element.properties;
  return (
    <span className="inline">
      {numberingBulletText && (
        <span className="not-italic font-bold mr-1.5">
          {numberingBulletText}
        </span>
      )}
      {data}
    </span>
  );
};

export default TextComponent;

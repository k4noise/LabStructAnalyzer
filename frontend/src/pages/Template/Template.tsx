import React from "react";

export const Template = () => {
  const dataStr = localStorage.getItem("pageData");
  let data = [];

  try {
    data = JSON.parse(dataStr) || [];
  } catch (e) {
    console.error("Failed to parse pageData", e);
  }

  return (
    <div>
      <h2 className="text-3xl font-medium text-center mb-10">
        Новая лабораторная работа
      </h2>
      {data.map((element, index) => (
        <React.Fragment key={index}>{TemplateFactory(element)}</React.Fragment>
      ))}
      <span className="ml-5 ml-10 ml-15 ml-20 ml-25 ml-30 ml-35 ml-40 ml-45"></span>
    </div>
  );
};

const TemplateFactory = (element) => {
  const numberingData = element.numberingBulletText ?? "";
  const nestingLevel = element.nestingLevel ? element.nestingLevel * 5 : 1;
  switch (element.type ?? element.contentType) {
    case "labPart":
      return (
        <h1 className={`font-medium ml-${nestingLevel}`}>{element.data}</h1>
      );
    case "image":
      return <img src={"/api/" + element.data} className="text-center"></img>;
    case "question":
      return (
        <span className={`font-italic my-3 ml-${nestingLevel}`}>
          {element.data}
        </span>
      );
    case "answer":
      return (
        <>
          <button className="px-2 py-1 ml-2 mb-2 border-solid rounded-xl border-2 dark:border-zinc-200 border-zinc-950">
            Настройка ответа
          </button>
          <br />
        </>
      );
    case "text":
      return (
        <p className={`ml-${nestingLevel} mb-3`}>
          {numberingData ? numberingData + " " + element.data : element.data}
        </p>
      );
    case "header":
      return (
        <h3 className={`font-medium my-3 ml-${nestingLevel}`}>
          {numberingData ? numberingData + " " + element.data : element.data}
        </h3>
      );
    case "table":
      return (
        <table>
          {element.data.map((row, indexX) => (
            <tr key={indexX}>
              {row.map((cellData, indexY) => {
                const isMerged =
                  cellData.merged &&
                  (cellData.merged.rows > 1 || cellData.merged.cols > 1);
                const rowSpan = isMerged ? cellData.rows : undefined;
                const colSpan = isMerged ? cellData.cols : undefined;

                return (
                  <td
                    key={`${indexX}-${indexY}`}
                    rowSpan={rowSpan}
                    colSpan={colSpan}
                    className="border-2 p-2"
                  >
                    {Array.isArray(cellData.data) ? (
                      cellData.data.map((nestedElement, nestedIndex) => (
                        <React.Fragment key={nestedIndex}>
                          {TemplateFactory(nestedElement)}
                        </React.Fragment>
                      ))
                    ) : (
                      <React.Fragment key={`${indexX}-${indexY}-cell`}>
                        {TemplateFactory(cellData.data)}
                      </React.Fragment>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </table>
      );
  }
  if (!element.data) {
    return;
  }

  return (
    <div className={`ml-${nestingLevel} my-5`}>
      {element.data.map((element, index) => (
        <React.Fragment key={index}>{TemplateFactory(element)}</React.Fragment>
      ))}
    </div>
  );
};

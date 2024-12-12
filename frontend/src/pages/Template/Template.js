import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import React from "react";
export const Template = () => {
    const dataStr = localStorage.getItem("pageData");
    let data = [];
    try {
        data = JSON.parse(dataStr) || [];
    }
    catch (e) {
        console.error("Failed to parse pageData", e);
    }
    return (_jsxs("div", { children: [_jsx("h2", { className: "text-3xl font-medium text-center mb-10", children: "\u041D\u043E\u0432\u0430\u044F \u043B\u0430\u0431\u043E\u0440\u0430\u0442\u043E\u0440\u043D\u0430\u044F \u0440\u0430\u0431\u043E\u0442\u0430" }), data.map((element, index) => (_jsx(React.Fragment, { children: TemplateFactory(element) }, index))), _jsx("span", { className: "ml-5 ml-10 ml-15 ml-20 ml-25 ml-30 ml-35 ml-40 ml-45" })] }));
};
const TemplateFactory = (element) => {
    const numberingData = element.numberingBulletText ?? "";
    const nestingLevel = element.nestingLevel ? element.nestingLevel * 5 : 1;
    switch (element.type ?? element.contentType) {
        case "labPart":
            return (_jsx("h1", { className: `font-medium ml-${nestingLevel}`, children: element.data }));
        case "image":
            return _jsx("img", { src: "/api/" + element.data, className: "text-center" });
        case "question":
            return (_jsx("span", { className: `font-italic my-3 ml-${nestingLevel}`, children: element.data }));
        case "answer":
            return (_jsxs(_Fragment, { children: [_jsx("button", { className: "px-2 py-1 ml-2 mb-2 border-solid rounded-xl border-2 dark:border-zinc-200 border-zinc-950", children: "\u041D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0430 \u043E\u0442\u0432\u0435\u0442\u0430" }), _jsx("br", {})] }));
        case "text":
            return (_jsx("p", { className: `ml-${nestingLevel} mb-3`, children: numberingData ? numberingData + " " + element.data : element.data }));
        case "header":
            return (_jsx("h3", { className: `font-medium my-3 ml-${nestingLevel}`, children: numberingData ? numberingData + " " + element.data : element.data }));
        case "table":
            return (_jsx("table", { children: element.data.map((row, indexX) => (_jsx("tr", { children: row.map((cellData, indexY) => {
                        const isMerged = cellData.merged &&
                            (cellData.merged.rows > 1 || cellData.merged.cols > 1);
                        const rowSpan = isMerged ? cellData.rows : undefined;
                        const colSpan = isMerged ? cellData.cols : undefined;
                        return (_jsx("td", { rowSpan: rowSpan, colSpan: colSpan, className: "border-2 p-2", children: Array.isArray(cellData.data) ? (cellData.data.map((nestedElement, nestedIndex) => (_jsx(React.Fragment, { children: TemplateFactory(nestedElement) }, nestedIndex)))) : (_jsx(React.Fragment, { children: TemplateFactory(cellData.data) }, `${indexX}-${indexY}-cell`)) }, `${indexX}-${indexY}`));
                    }) }, indexX))) }));
    }
    if (!element.data) {
        return;
    }
    return (_jsx("div", { className: `ml-${nestingLevel} my-5`, children: element.data.map((element, index) => (_jsx(React.Fragment, { children: TemplateFactory(element) }, index))) }));
};

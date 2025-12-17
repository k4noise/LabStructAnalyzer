import React, { memo, useMemo } from "react";
import { TemplateElementModel } from "../../model/templateElement";
import AnswerContext, { AnswerContextProps } from "../../context/AnswerContext";
import AnswerComponent from "./AnswerComponent";
import HeaderComponent from "./HeaderComponent";
import ImageComponent from "./ImageComponent";
import QuestionComponent from "./QuestionComponent";
import TableComponent from "./TableComponent";
import TextComponent from "./TextComponent";
import RowComponent from "./RowComponent";
import CellComponent from "./CellComponent";
import { UUID } from "crypto";

type TreeNode = TemplateElementModel & {
  children: TreeNode[];
  id: UUID;
};

type BaseElementProps<T extends TemplateElementModel> = {
  element: T;
  level: number;
  children: TreeNode[];
  renderChild: (child: TreeNode) => React.ReactNode;
};

const componentMap: Record<string, React.FC<BaseElementProps<any>>> = {
  text: memo(TextComponent),
  image: memo(ImageComponent),
  header: memo(HeaderComponent),
  question: memo(QuestionComponent),
  table: memo(TableComponent),
  row: memo(RowComponent),
  cell: memo(CellComponent),
  answer: memo(AnswerComponent),
};

const buildElementTree = (flatElements: TemplateElementModel[]): TreeNode[] => {
  const elementMap = new Map<string, TreeNode>();
  const rootElements: TreeNode[] = [];

  flatElements.forEach((el) => {
    elementMap.set(el.id, { ...el, children: [] });
  });

  flatElements.forEach((el) => {
    const treeNode = elementMap.get(el.id)!;
    if (el.parent_id === null) {
      rootElements.push(treeNode);
    } else {
      const parent = elementMap.get(el.parent_id);
      if (parent) {
        parent.children.push(treeNode);
      } else {
        console.error(
          `Нарушение иерархии: Родитель с id ${el.parent_id} не найден для элемента ${el.id}. Элемент будет проигнорирован.`
        );
      }
    }
  });

  return rootElements;
};

interface TemplateElementsProps {
  elements: TemplateElementModel[];
  answerContextProps: AnswerContextProps;
}

const TemplateElements: React.FC<TemplateElementsProps> = memo(
  ({ elements, answerContextProps }) => {
    const elementTree = useMemo(() => buildElementTree(elements), [elements]);

    const renderNode = (element: TreeNode, level: number): React.ReactNode => {
      const Component = componentMap[element.type];

      if (Component) {
        return (
          <Component
            key={element.id}
            element={element}
            level={level}
            children={element.children}
            renderChild={(child) => renderNode(child, level + 1)}
          />
        );
      }

      if (element.children.length > 0) {
        return (
          <React.Fragment key={element.id}>
            {element.children.map((child) => renderNode(child, level + 1))}
          </React.Fragment>
        );
      }

      console.warn(`Компонент для типа "${element.type}" не найден.`);
      return null;
    };

    return (
      <AnswerContext.Provider value={answerContextProps}>
        {elementTree.map((rootElement) => renderNode(rootElement, 0))}

        <span className="hidden ml-4 ml-8 ml-12 ml-16 ml-20 my-4 my-8 my-12 my-16"></span>
      </AnswerContext.Provider>
    );
  }
);

TemplateElements.displayName = "TemplateElements";

export default TemplateElements;
export type { BaseElementProps };

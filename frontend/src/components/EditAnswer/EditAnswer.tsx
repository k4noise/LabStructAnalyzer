import {
  AnswerElement,
  TemplateElementModel,
} from "../../model/templateElement";
import Textarea from "../Textarea/TextareaComponent";
import { zodResolver } from "@hookform/resolvers/zod";
import { FieldValues, useForm } from "react-hook-form";
import { AnswerEdit } from "../../model/answer";
import EditAnswerSchema from "./EditAnswerSchema";
import Button from "../Button/Button";

interface EditAnswerModalProps {
  element: AnswerElement | null;
  onSave: (
    id: string,
    element: Partial<TemplateElementModel["properties"]>
  ) => void;
}

const EditAnswer = ({
  element,
  onSave: onSaveChanges,
}: EditAnswerModalProps) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AnswerEdit>({
    resolver: zodResolver(EditAnswerSchema),
  });

  const onFormSend = (data: FieldValues) => {
    onSaveChanges(element.element_id, data);
  };

  return (
    <form onSubmit={handleSubmit(onFormSend)}>
      <h3 className="text-xl font-bold text-center mb-4">Настройка ответа</h3>
      <label className="block mb-3">
        id:
        <Textarea
          className="ml-3 w-60 align-top bg-transparent border-b-2  border-zinc-950 dark:border-zinc-200 overflow-hidden"
          placeholder="Пользовательское имя"
          value={element?.properties?.customId ?? ""}
          minRowsCount={1}
          validationOptions={register("customId")}
        />
      </label>
      {errors.customId?.message && (
        <span className="text-center mb-3 bg-gradient-to-r from-transparent via-yellow-400/50 to-transparent">
          {errors.customId?.message}
        </span>
      )}
      <label className="block mb-3">
        Вес [0-20]:
        <input
          type="number"
          min={0}
          max={20}
          defaultValue={element?.properties.weight ?? 1}
          className="ml-3 bg-transparent border-b-2 border-zinc-950 dark:border-zinc-200"
          {...register("weight")}
        />
      </label>
      {errors.weight?.message && (
        <p className="text-center mb-3 bg-gradient-to-r from-transparent via-yellow-400/50 to-transparent">
          {errors.weight?.message}
        </p>
      )}
      <label className="block mb-3">
        Эталонный ответ:
        <Textarea
          className="ml-3 w-60 align-top bg-transparent border-b-2  border-zinc-950 dark:border-zinc-200 overflow-hidden"
          placeholder="Ответ"
          value={element?.properties?.refAnswer ?? ""}
          minRowsCount={1}
          validationOptions={register("refAnswer")}
        />
      </label>
      <Button text="Сохранить" type="submit" classes="block ml-auto" />
    </form>
  );
};

export default EditAnswer;

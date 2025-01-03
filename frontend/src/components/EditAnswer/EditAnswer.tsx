import { AnswerElement, TemplateElementModel } from "../../model/template";
import Textarea from "../Textarea/TextareaComponent";
import { zodResolver } from "@hookform/resolvers/zod";
import { FieldValues, useForm } from "react-hook-form";
import { AnswerEdit } from "../../model/answer";
import EditAnswerSchema from "./EditAnswerSchema";

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
      <h3 className="text-xl font-medium text-center mb-4">Настройка ответа</h3>
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
        Краткий ответ:
        <input
          type="checkbox"
          className="ml-3"
          defaultChecked={element?.properties.simple}
          {...register("simple")}
        />
      </label>
      <button
        className="block px-2 py-1 ml-auto border-solid rounded-xl border-2 dark:border-zinc-200 border-zinc-950"
        type="submit"
      >
        Сохранить
      </button>
    </form>
  );
};

export default EditAnswer;

import * as zod from "zod";

const MIN_POSSIBLE_ANSWER_WEIGHT = 0;
const MAX_POSSIBLE_ANSWER_WEIGHT = 20;

const EditAnswerSchema = zod.object({
  customId: zod
    .string()
    .optional()
    .refine(
      (value) => !value || (value.length >= 5 && /^[a-zA-Z\d_]+$/.test(value)),
      "Идентификатор должен быть не менее 5 символов и состоять только из латинских букв, цифр и нижнего подчеркивания"
    ),
  weight: zod.coerce
    .number()
    .min(MIN_POSSIBLE_ANSWER_WEIGHT, "Вес не может быть меньше нуля")
    .max(MAX_POSSIBLE_ANSWER_WEIGHT, "Вес не может быть более 20"),
  answerType: zod.string(),
});

export default EditAnswerSchema;

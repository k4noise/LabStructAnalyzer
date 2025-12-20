from typing import Dict, Any
from transformers import T5Tokenizer
import ctranslate2

from labstructanalyzer.schemas.hint import HintGenerationRequest


class HintGenerator:
    """Генератор подсказок/вопросов на основе контекста, ответа студента и описания ошибки."""

    def __init__(
            self,
            tokenizer: T5Tokenizer,
            model: ctranslate2.Translator,
    ) -> None:
        self.tokenizer = tokenizer
        self.model = model
        self.max_context_len = 150
        self.max_answer_len = 100

    def _post_process(self, text: str) -> str:
        """Чистка ответа модели от лишних префиксов и пробелов"""
        text = (text or "").strip()

        prefixes = ["[ВОПРОС]", "[ПОДСКАЗКА]"]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()

        return " ".join(text.split())

    def generate(
            self,
            context: HintGenerationRequest,
            **generation_params: Any
    ) -> str | None:
        """Генерирует подсказку по ответу пользователя"""
        if context is None:
            return None

        main_input = self._build_prompt(' '.join(context.theory), context.answer,
                                        context.error_explanation)

        default_params: Dict[str, Any] = {
            "beam_size": 3,
            "max_decoding_length": 60,
            "repetition_penalty": 1.1,
            "no_repeat_ngram_size": 2,
            "length_penalty": 0.8,
        }
        params = {**default_params, **generation_params}

        input_text = f"ask | {main_input}"

        input_ids = self.tokenizer.encode(input_text)
        token_strings = self.tokenizer.convert_ids_to_tokens(input_ids)

        results = self.model.translate_batch([token_strings], **params)

        if not results or not results[0].hypotheses:
            return None

        output_tokens = results[0].hypotheses[0]
        generated_text = self.tokenizer.convert_tokens_to_string(output_tokens)

        return self._post_process(generated_text)

    def _build_prompt(self, context: str, student_answer: str, error: str) -> str:
        """Формирует промпт для модели."""
        context_trimmed = (context or "")[:self.max_context_len]
        answer_trimmed = (student_answer or "")[:self.max_answer_len]
        error = error or ""

        return (
            f"[ЗАДАЧА] {context_trimmed}\n"
            f"[ОТВЕТ СТУДЕНТА] {answer_trimmed}\n"
            f"[ОШИБКА] {error}\n"
            f"[ВОПРОС]"
        ) if context else (f"[НЕПРАВИЛЬНЫЙ ОТВЕТ] {answer_trimmed}\n"
                           f"[ОШИБКА] {error}\n"
                           f"[ВОПРОС]")

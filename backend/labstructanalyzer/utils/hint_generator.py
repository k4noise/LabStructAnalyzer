import re
from typing import Any, Optional, List
from llama_cpp import Llama


class HintGenerator:
    """Генератор подсказок/вопросов на основе контекста, ответа студента и описания ошибки."""

    def __init__(self, model_path: str) -> None:
        self.model = Llama(
            model_path=model_path,
            n_gpu_layers=-1,
            n_ctx=2048,
            verbose=False
        )
        self.max_context_len = 600

    def _post_process(self, text: str) -> str:
        if not text:
            return ""

        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

        first_line = ""
        for line in text.splitlines():
            line = line.strip()
            if line:
                first_line = line
                break
        if not first_line:
            return ""

        first_line = re.sub(
            r'^(Вопрос|Подсказка|Тьютор|Assistant|Ответ)\s*:?\s*',
            '',
            first_line,
            flags=re.IGNORECASE
        ).strip()

        if "?" in first_line:
            first_line = first_line.split("?", 1)[0].strip()

        return (first_line + "?") if first_line else ""

    def _build_prompt(self, theory: str, student_answer: str, error: str) -> str:
        theory = theory[: self.max_context_len]

        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Сравни текст и ответ.
Найди несовпадение и задай один вопрос (до 7 слов), чтобы студент сам понял, в чем ошибка.
Не подсказывай ответ. Только один вопрос.<|eot_id|><|start_header_id|>user<|end_header_id|>

ДАННЫЕ: {theory}
СТУДЕНТ НАПИСАЛ: {student_answer}
ПРОБЛЕМА: {error}

Вопрос к студенту: """

    def generate(self, context: Any) -> Optional[str]:
        if context is None:
            return None

        theory_list: List[str] = getattr(context, "theory", []) or []
        theory_text = "\n\n".join(t for t in theory_list if t)

        student_answer = getattr(context, "answer", "") or ""
        error = getattr(context, "error_explanation", "") or ""

        prompt_text = self._build_prompt(
            theory_text,
            student_answer,
            error
        )
        print(context)
        print(prompt_text)

        params = {
            "max_tokens": 40,
            "temperature": 0.2,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "stop": ["<|eot_id|>", "###"],
            "echo": False
        }

        try:
            output = self.model(prompt_text, **params)
            raw_text = output["choices"][0]["text"]

            hint = self._post_process(raw_text)
            return hint if len(hint) > 3 else None
        except Exception as e:
            print(f"Ошибка: {e}")
            return None

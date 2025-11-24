import uuid
import unittest
from unittest.mock import MagicMock, AsyncMock

from sqlmodel.ext.asyncio.session import AsyncSession

from labstructanalyzer.models.answer import Answer
from labstructanalyzer.schemas.answer import UpdateAnswerDataRequest, UpdateAnswerScoresRequest, NewAnswerData
from labstructanalyzer.repository.answer import AnswerRepository


class TestAnswerRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Настраивает тестовое окружение перед каждым тестом"""
        self.session = MagicMock(spec=AsyncSession)
        self.session.exec = AsyncMock()
        self.session.execute = AsyncMock()
        self.session.add_all = MagicMock()
        self.session.flush = AsyncMock()
        self.repository = AnswerRepository(self.session)
        self.report_id = uuid.uuid4()

    def _create_mock_answer(self, answer_id, element_id, score, data, pre_grade):
        """Создает мок-объект ответа"""
        mock_row = MagicMock(spec=Answer)
        mock_row.id = answer_id
        mock_row.element_id = element_id
        mock_row.score = score
        mock_row.data = data
        mock_row.pre_grade = pre_grade
        mock_row.report_id = self.report_id
        return mock_row

    def _setup_session_exec_result(self, answers: list):
        """Настраивает результат для session.exec"""
        mock_result = MagicMock()
        mock_result.all.return_value = answers
        self.session.exec.return_value = mock_result

    async def test_get_all_by_report_successful(self):
        """Успешное получение всех ответов для отчета"""
        answer_id = uuid.uuid4()
        mock_answer = self._create_mock_answer(answer_id, uuid.uuid4(), 5, "{}", "A")
        self._setup_session_exec_result([mock_answer])

        result = await self.repository.get_all_by_report(self.report_id)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, answer_id)
        self.session.exec.assert_called_once()

    async def test_get_all_by_report_empty(self):
        """Возврат пустого списка при отсутствии ответов"""
        self._setup_session_exec_result([])

        result = await self.repository.get_all_by_report(self.report_id)

        self.assertEqual(result, [])
        self.session.exec.assert_called_once()

    async def test_bulk_create_successful(self):
        """Корректное создание нескольких ответов"""
        first_uid = uuid.uuid4()
        second_uid = uuid.uuid4()

        answers_data = [
            NewAnswerData(element_id=first_uid, score=5, data={}, pre_grade={}),
            NewAnswerData(element_id=second_uid, score=3, data={}, pre_grade={})
        ]
        expected_ids = [first_uid, second_uid]

        created_answers = []

        def add_all_side_effect(answers):
            for i, answer in enumerate(answers):
                answer.id = expected_ids[i]
                created_answers.extend(answers)

        self.session.add_all.side_effect = add_all_side_effect

        result = await self.repository.bulk_create(self.report_id, answers_data)

        self.assertEqual(result, expected_ids)
        self.session.add_all.assert_called_once()
        self.session.flush.assert_awaited()

    async def test_bulk_create_empty_list(self):
        """Создание при пустом списке возвращает пустой список"""
        result = await self.repository.bulk_create(self.report_id, [])

        self.assertEqual(result, [])
        self.session.add_all.assert_called_once_with([])
        self.session.flush.assert_awaited()

    async def test_bulk_update_data_successful(self):
        """Успешное обновление данных нескольких ответов"""
        update_data = [
            UpdateAnswerDataRequest(id=uuid.uuid4(), data={"new_data": 123}),
            UpdateAnswerDataRequest(id=uuid.uuid4(), data={"another_data": True})
        ]

        mock_result = MagicMock()
        mock_result.rowcount = 2
        self.session.execute.return_value = mock_result

        result = await self.repository.bulk_update_data(self.report_id, update_data)

        self.assertEqual(result, 2)
        self.session.execute.assert_called_once()

        call_args = self.session.execute.call_args[0][0]
        self.assertIn('UPDATE', str(call_args))

    async def test_bulk_update_data_empty_list(self):
        """Обновление пустого списка пропускается"""
        result = await self.repository.bulk_update_data(self.report_id, [])

        self.assertEqual(result, 0)
        self.session.execute.assert_not_called()

    async def test_bulk_update_data_partial_update(self):
        """Частичное обновление - некоторые ID не существуют"""
        update_data = [
            UpdateAnswerDataRequest(id=uuid.uuid4(), data={}),
            UpdateAnswerDataRequest(id=uuid.uuid4(), data={"newer": True})
        ]

        mock_result = MagicMock()
        mock_result.rowcount = 1
        self.session.execute.return_value = mock_result

        result = await self.repository.bulk_update_data(self.report_id, update_data)

        self.assertEqual(result, 1)
        self.session.execute.assert_called_once()

    async def test_bulk_update_scores_successful(self):
        """Успешное обновление оценок нескольких ответов"""
        update_scores = [
            UpdateAnswerScoresRequest(id=uuid.uuid4(), score=10),
            UpdateAnswerScoresRequest(id=uuid.uuid4(), score=20)
        ]

        mock_result = MagicMock()
        mock_result.rowcount = 2
        self.session.execute.return_value = mock_result

        result = await self.repository.bulk_update_scores(self.report_id, update_scores)

        self.assertEqual(result, 2)
        self.session.execute.assert_called_once()

        call_args = self.session.execute.call_args[0][0]
        self.assertIn('UPDATE', str(call_args))

    async def test_bulk_update_scores_empty_list(self):
        """Обновление пустого списка пропускается"""
        result = await self.repository.bulk_update_scores(self.report_id, [])

        self.assertEqual(result, 0)
        self.session.execute.assert_not_called()

    async def test_bulk_update_scores_partial_update(self):
        """Частичное обновление оценок - некоторые ID не существуют"""
        update_scores = [
            UpdateAnswerScoresRequest(id=uuid.uuid4(), score=100),
            UpdateAnswerScoresRequest(id=uuid.uuid4(), score=200)
        ]

        mock_result = MagicMock()
        mock_result.rowcount = 1
        self.session.execute.return_value = mock_result

        result = await self.repository.bulk_update_scores(self.report_id, update_scores)

        self.assertEqual(result, 1)
        self.session.execute.assert_called_once()


if __name__ == '__main__':
    unittest.main()

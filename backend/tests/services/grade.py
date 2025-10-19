import unittest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch, Mock

from labstructanalyzer.domain.report_status import ReportStatus
from labstructanalyzer.exceptions.no_entity import ReportNotFoundException
from labstructanalyzer.models.user_model import User, UserRole
from labstructanalyzer.schemas.answer import UpdateAnswerScoresRequest, AnswerResponse
from labstructanalyzer.schemas.template import FullWorkResponse, TemplateDetailResponse
from labstructanalyzer.services.grade import GradeService


class TestGradeService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Создание мок-сервисов и тестовых данных"""
        self.report_service = MagicMock()
        self.report_service.get = AsyncMock()
        self.report_service.submit = AsyncMock()
        self.report_service.grade = AsyncMock()

        self.background_task_service = MagicMock()
        self.background_task_service.submit = MagicMock()

        self.ags_service = MagicMock()
        self.ags_service.set_grade = MagicMock()

        self.nrps_service = MagicMock()

        self.mock_logger_instance = MagicMock()
        mock_global_logger = MagicMock()
        mock_global_logger.return_value.get_logger.return_value = self.mock_logger_instance
        patcher = patch('labstructanalyzer.services.grade.GlobalLogger', mock_global_logger)
        self.addCleanup(patcher.stop)
        patcher.start()

        self.service = GradeService(
            self.report_service,
            self.background_task_service,
            self.ags_service,
            self.nrps_service
        )

        self.user = User(
            sub="grader123",
            course_id="course456",
            roles=[UserRole.TEACHER],
            launch_id="launch789"
        )
        self.student = User(
            sub="student123",
            course_id="course456",
            roles=[UserRole.STUDENT],
            launch_id="launch789"
        )
        self.report_id = uuid.uuid4()

        self.template = TemplateDetailResponse(
            id=uuid.uuid4(),
            name="Test Template",
            max_score=100,
            elements=[],
            user=self.user
        )

        self.answers = [
            AnswerResponse(
                element_id=uuid.uuid4(),
                data={},
                score=8,
                weight=1,
                root_id=None
            ),
            AnswerResponse(
                element_id=uuid.uuid4(),
                data={},
                score=6,
                weight=1,
                root_id=None
            )
        ]

        self.report = FullWorkResponse(
            report_id=self.report_id,
            author_id=self.student.sub,
            status=ReportStatus.SUBMITTED,
            template=self.template,
            answers=self.answers,
            user=self.user
        )

    @patch('labstructanalyzer.services.grade.PreGraderService')
    async def test_send_to_grade_success(self, mock_pre_grader_class):
        """Успешная отправка отчета на проверку"""
        mock_pre_grader_instance = Mock()
        mock_pre_grader_class.return_value = mock_pre_grader_instance
        self.report_service.get.return_value = self.report

        await self.service.send_to_grade(self.user, self.report_id)

        self.report_service.get.assert_awaited_once_with(self.user, self.report_id, self.nrps_service)
        self.report_service.submit.assert_awaited_once_with(self.user, self.report_id)

        mock_pre_grader_class.assert_called_once_with(self.report.answers)

        self.background_task_service.submit.assert_called_once_with(mock_pre_grader_instance.grade)

        updated_report = await self.report_service.get(self.user, self.report_id, self.nrps_service)
        self.assertEqual(updated_report.status, ReportStatus.SUBMITTED)

        self.mock_logger_instance.info.assert_called_once_with(
            f"Отчет отправлен на проверку: id {self.report_id}"
        )

    async def test_send_to_grade_report_not_found(self):
        """Отправка несуществующего отчета на проверку вызывает исключение"""
        self.report_service.get.side_effect = ReportNotFoundException()

        with self.assertRaises(ReportNotFoundException):
            await self.service.send_to_grade(self.user, self.report_id)

        self.report_service.submit.assert_not_awaited()
        self.background_task_service.submit.assert_not_called()
        self.mock_logger_instance.info.assert_not_called()

    async def test_grade_success_with_simple_scores(self):
        """Успешная оценка отчета с простыми оценками"""
        answers = [
            AnswerResponse(
                id=uuid.uuid4(),
                element_id=uuid.uuid4(),
                data={},
                weight=8,
                root_id=None
            ),
            AnswerResponse(
                id=uuid.uuid4(),
                element_id=uuid.uuid4(),
                data={},
                weight=6,
                root_id=None
            )
        ]
        scores = [
            UpdateAnswerScoresRequest(id=answers[0].id, score=1),
            UpdateAnswerScoresRequest(id=answers[1].id, score=0)
        ]
        report = FullWorkResponse(
            report_id=self.report_id,
            author_id=self.student.sub,
            status=ReportStatus.SUBMITTED,
            template=self.template,
            answers=answers,
            user=self.user
        )
        self.report_service.get.return_value = report

        await self.service.grade(self.user, self.report_id, scores)

        self.report_service.get.assert_awaited_once_with(self.user, self.report_id, self.nrps_service)
        self.ags_service.set_grade.assert_called_once_with(
            self.template,
            self.student.sub,
            57.14
        )

        args, _ = self.report_service.grade.call_args
        update_info = args[2]
        self.assertEqual(update_info.id, self.report_id)
        self.assertEqual(update_info.grader_id, self.user.sub)
        self.assertEqual(update_info.new_scores, scores)
        self.assertEqual(update_info.final_score, 57.14)

        self.report_service.grade.assert_awaited_once()
        self.mock_logger_instance.info.assert_called_with(
            f"Оценен отчет: id {self.report_id}"
        )

    async def test_grade_success_with_grouped_scores(self):
        """Успешная оценка отчета сгруппированными оценками"""
        root_id = uuid.uuid4()
        answers = [
            AnswerResponse(
                id=uuid.uuid4(),
                element_id=uuid.uuid4(),
                data={},
                weight=10,
                root_id=root_id
            ),
            AnswerResponse(
                id=uuid.uuid4(),
                element_id=uuid.uuid4(),
                data={},
                weight=8,
                root_id=root_id
            ),
            AnswerResponse(
                id=uuid.uuid4(),
                element_id=uuid.uuid4(),
                data={},
                weight=6,
                root_id=None
            )
        ]
        scores = [
            UpdateAnswerScoresRequest(id=answers[0].id, score=1),
            UpdateAnswerScoresRequest(id=answers[1].id, score=0),
            UpdateAnswerScoresRequest(id=answers[2].id, score=1)
        ]
        report = FullWorkResponse(
            report_id=self.report_id,
            author_id=self.student.sub,
            status=ReportStatus.SUBMITTED,
            template=self.template,
            answers=answers,
            user=self.user
        )
        self.report_service.get.return_value = report

        await self.service.grade(self.user, self.report_id, scores)

        self.ags_service.set_grade.assert_called_once_with(
            self.template,
            self.student.sub,
            73.33
        )

    async def test_grade_success_with_zero_scores(self):
        """Успешная оценка отчета с нулевыми оценками"""
        answers = [
            AnswerResponse(
                element_id=uuid.uuid4(),
                data={},
                score=0,
                weight=1,
                root_id=None
            ),
            AnswerResponse(
                element_id=uuid.uuid4(),
                data={},
                score=0,
                weight=1,
                root_id=None
            )
        ]
        scores = [
            UpdateAnswerScoresRequest(id=uuid.uuid4(), score=0),
            UpdateAnswerScoresRequest(id=uuid.uuid4(), score=0)
        ]
        report = FullWorkResponse(
            report_id=self.report_id,
            author_id=self.student.sub,
            status=ReportStatus.SUBMITTED,
            template=self.template,
            answers=answers,
            user=self.user
        )
        self.report_service.get.return_value = report

        await self.service.grade(self.user, self.report_id, scores)

        self.ags_service.set_grade.assert_called_once_with(
            self.template,
            self.student.sub,
            0
        )

    async def test_grade_report_not_found(self):
        """Оценка несуществующего отчета вызывает исключение"""
        self.report_service.get.side_effect = ReportNotFoundException()

        with self.assertRaises(ReportNotFoundException):
            await self.service.grade(self.user, self.report_id, [])

        self.ags_service.set_grade.assert_not_called()
        self.report_service.grade.assert_not_awaited()

    async def test_grade_with_different_weights(self):
        """Оценка отчета с разными весами ответов"""
        answers = [
            AnswerResponse(
                id=uuid.uuid4(),
                element_id=uuid.uuid4(),
                data={},
                weight=10,
                root_id=None
            ),
            AnswerResponse(
                id=uuid.uuid4(),
                element_id=uuid.uuid4(),
                data={},
                weight=6,
                root_id=None
            )
        ]
        scores = [
            UpdateAnswerScoresRequest(id=answers[0].id, score=1),
            UpdateAnswerScoresRequest(id=answers[1].id, score=0)
        ]
        report = FullWorkResponse(
            report_id=self.report_id,
            author_id=self.student.sub,
            status=ReportStatus.SUBMITTED,
            template=self.template,
            answers=answers,
            user=self.user
        )
        self.report_service.get.return_value = report

        await self.service.grade(self.user, self.report_id, scores)

        self.ags_service.set_grade.assert_called_once_with(
            self.template,
            self.student.sub,
            62.5
        )

    async def test_grade_with_zero_weights(self):
        """Оценка отчета с нулевыми весами"""
        answers = [
            AnswerResponse(
                id=uuid.uuid4(),
                element_id=uuid.uuid4(),
                data={},
                weight=0,
                root_id=None
            )
        ]
        scores = [
            UpdateAnswerScoresRequest(id=answers[0].id, score=10)
        ]
        report = FullWorkResponse(
            report_id=self.report_id,
            author_id=self.student.sub,
            status=ReportStatus.SUBMITTED,
            template=self.template,
            answers=answers,
            user=self.user
        )
        self.report_service.get.return_value = report

        await self.service.grade(self.user, self.report_id, scores)

        self.ags_service.set_grade.assert_called_once_with(
            self.template,
            self.student.sub,
            0
        )

    async def test_grade_with_empty_scores(self):
        """Оценка отчета с пустым списком оценок"""
        report = FullWorkResponse(
            report_id=self.report_id,
            author_id=self.student.sub,
            status=ReportStatus.SUBMITTED,
            template=self.template,
            answers=[],
            user=self.user
        )
        self.report_service.get.return_value = report

        await self.service.grade(self.user, self.report_id, [])

        self.ags_service.set_grade.assert_called_once_with(
            self.template,
            self.student.sub,
            0
        )


if __name__ == '__main__':
    unittest.main()

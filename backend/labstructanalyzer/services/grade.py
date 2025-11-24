import uuid
from typing import Sequence

from labstructanalyzer.core.database import get_session
from labstructanalyzer.core.logger import GlobalLogger
from labstructanalyzer.domain.report import UpdateGradeInfo
from labstructanalyzer.models.user_model import User
from labstructanalyzer.repository.answer import AnswerRepository
from labstructanalyzer.repository.report import ReportRepository
from labstructanalyzer.schemas.answer import UpdateAnswerScoresRequest, AnswerResponse
from labstructanalyzer.schemas.template import FullWorkResponse
from labstructanalyzer.services.answer import AnswerService
from labstructanalyzer.services.background_task import BackgroundTaskService
from labstructanalyzer.services.lti.ags import AgsService
from labstructanalyzer.services.lti.nrps import NrpsService
from labstructanalyzer.services.pre_grader import PreGraderService
from labstructanalyzer.services.report import ReportService


class GradeService:
    def __init__(self, report_service: ReportService, background_task_service: BackgroundTaskService,
                 ags_service: AgsService, nrps_service: NrpsService):
        self.report_service = report_service
        self.background_task_service = background_task_service
        self.ags_service = ags_service
        self.nrps_service = nrps_service
        self.logger = GlobalLogger().get_logger(__name__)

    async def send_to_grade(self, user: User, report_id: uuid.UUID):
        """Отправляет отчет на проверку с инициализацией предварительной проверки"""
        report = await self.report_service.get(user, report_id, self.nrps_service)
        await self.report_service.submit(user, report_id)
        self.background_task_service.enqueue(self._pre_grade_with_save, report)
        self.logger.info(f"Отчет отправлен на проверку: id {report_id}")

    async def grade(self, user: User, report_id: uuid.UUID, scores: Sequence[UpdateAnswerScoresRequest]):
        """Сохранить оценку после проверки преподавателем/ассистентом"""
        report = await self.report_service.get(user, report_id, self.nrps_service)
        score_map = {score.id: score.score for score in scores}
        updated_answers = [
            answer.model_copy(update={'score': score_map.get(answer.id, answer.score)})
            for answer in report.answers
        ]

        final_score = await self._calc_final_score(updated_answers, report.template.max_score)
        report_updates = UpdateGradeInfo(
            id=report_id,
            grader_id=user.sub,
            new_scores=scores,
            final_score=final_score
        )

        self.ags_service.set_grade(report.template, report.author_id, final_score)
        await self.report_service.grade(user, report_id, report_updates)
        self.logger.info(f"Оценен отчет: id {report_id}")

    async def _calc_final_score(self, answers: Sequence[AnswerResponse], max_score: int):
        """Вычислить итоговый балл отчета с учетом группировки ответов по родителям"""
        group_weights = {None: 1}
        for answer in answers:
            if answer.root_id:
                group_weights[answer.root_id] = group_weights.get(answer.root_id, 0) + 1

        total_weighted_score = 0
        total_weight = 0

        for answer in answers:
            current_weight = answer.weight / group_weights[answer.root_id]
            total_weighted_score += (answer.score or 0) * current_weight
            total_weight += current_weight

        if total_weight == 0:
            return 0

        normalized_score = total_weighted_score / total_weight
        return round(normalized_score * max_score, 2)

    def _calc_answer_score(self, answer: AnswerResponse, group_weight: int):
        """Вычислить итоговый балл ответа с поправкой на количество ответов в родителе"""
        return answer.score * answer.weight * (1 / group_weight)

    async def _pre_grade_with_save(self, report: FullWorkResponse):
        """Вычислить и сохранить предварительные результаты"""
        session = get_session()
        report_service = ReportService(ReportRepository(session), AnswerService(AnswerRepository(session)))
        results = PreGraderService(report.answers).grade_many()
        await report_service.save(report.user, report.id, results)

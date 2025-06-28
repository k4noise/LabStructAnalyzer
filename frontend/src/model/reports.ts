import { AnswerModel } from "./answer";

export interface AllReportsInfo {
  template_name: string;
  max_score: number;
  reports: MinimalReportInfoDto[];
}

export interface MinimalReportInfoDto {
  template_id: string;
  report_id: string;
  date: number;
  status: string;
  author_name: string;
  score?: number;
}

export interface ReportInfoDto extends MinimalReportInfoDto {
  can_edit: boolean;
  can_grade: boolean;
  author_name: string;
  grader_name?: string;
  answers: AnswerModel[];
}

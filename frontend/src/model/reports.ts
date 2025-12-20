import { AnswerModel } from "./answer";
import { TemplateStructure } from "./template";

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
  template: TemplateStructure;
  id: string;
  answers: AnswerModel[];
  grader_name?: string;
  links: object;
}

import { TemplateElement } from "./templateElement";

interface HALLink {
  href: string;
}

interface TemplateUpdateRequest {
  name?: string;
  max_score?: number;
  elements?: []; //todo дополнить
}

interface MinimalReportResponse {
  id: string;
  status: string;
  score?: number;
}

interface TemplateStructure {
  id: string;
  name: string;
  max_score: number;
  is_draft?: boolean;
}

interface TemplateDetailResponse extends TemplateStructure {
  embedded: {
    elements: TemplateElement[];
  };
  links: {
    self: HALLink;
    update?: HALLink; // только для teacher
    publish?: HALLink; // только для teacher, если черновик
    delete?: HALLink; // только для teacher
    all: HALLink;
  };
}

interface TemplateCourseSummary {
  id: string;
  name: string;
  isDraft: boolean;
  reports: MinimalReportResponse[];
  links: {
    self: HALLink;
    get_template?: HALLink; // только для teacher
    get_reports?: HALLink; // только для instructor
    create_report?: HALLink; // только для student
  };
}

interface TemplateCourseCollection {
  links: {
    self: HALLink;
    add_template?: HALLink; // только для teacher
  };
  embedded: {
    templates: TemplateCourseSummary[];
  };
  courseName: string;
}

export type { TemplateDetailResponse, TemplateCourseCollection };

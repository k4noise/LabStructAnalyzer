interface HALLink {
  href: string;
}

// Минимальный отчет (дополни по реальным полям)
interface MinimalReportResponse {
  id: string;
  status: string;
  score?: number;
}

// Сводка по шаблону
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

// Вся коллекция
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

export { TemplateCourseCollection };

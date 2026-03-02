/** TypeScript types matching the FastAPI Pydantic models. */

export interface ExperienceEntry {
  job_title: string;
  company: string;
  start_date: string;
  end_date: string;
  responsibilities: string[];
}

export interface EducationEntry {
  degree: string;
  institution: string;
  end_date: string;
}

export interface ResumeJSON {
  candidate_name: string;
  email: string;
  phone: string;
  summary: string;
  skills: string[];
  experience: ExperienceEntry[];
  education: EducationEntry[];
  certifications: string[];
  total_years_experience: number;
}

export interface JDJSON {
  job_title: string;
  company: string;
  location: string;
  summary: string;
  required_skills: string[];
  preferred_skills: string[];
  minimum_experience_years: number;
  responsibilities: string[];
  education_requirements: string[];
}

export interface SkillEvidence {
  skill: string;
  evidence: string[];
}

export interface ComponentScores {
  required_skills_score: number;
  preferred_skills_score: number;
  experience_score: number;
  responsibilities_score: number;
  education_score: number;
}

export interface MatchReportJSON {
  overall_score: number;
  component_scores: ComponentScores;
  matched_skills: SkillEvidence[];
  missing_skills: SkillEvidence[];
  strengths: string[];
  weak_areas: string[];
  improvement_suggestions: string[];
  rationale: string;
  resume_name: string;
  job_title: string;
}

export interface FeedbackResponse {
  suggestions: string[];
  rewritten_bullets: string[];
}

/** Combined result passed to the UI after the full pipeline runs. */
export interface AnalysisResult {
  match: MatchReportJSON;
  feedback: FeedbackResponse;
}

import axios from "axios";
import type {
  ResumeJSON,
  JDJSON,
  MatchReportJSON,
  FeedbackResponse,
  AnalysisResult,
} from "../types/api";

export type { AnalysisResult };

export type StepId = "parse" | "match" | "feedback";
export type StepStatus = "idle" | "active" | "done" | "error";
export type OnStep = (step: StepId, status: StepStatus) => void;

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  headers: { "Content-Type": "application/json" },
});

export async function uploadResumePdf(file: File): Promise<{ resume_text: string }> {
  const form = new FormData();
  form.append("file", file);
  try {
    const { data } = await api.post<{ resume_text: string }>(
      "/api/parse-resume-pdf",
      form,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return data;
  } catch (err: unknown) {
    if (axios.isAxiosError(err)) {
      const detail = err.response?.data?.detail;
      throw new Error(
        typeof detail === "string" ? detail : "PDF extraction failed."
      );
    }
    throw new Error("PDF extraction failed.");
  }
}

async function parseResume(resumeText: string): Promise<ResumeJSON> {
  const { data } = await api.post<ResumeJSON>("/api/parse-resume", {
    resume_text: resumeText,
  });
  return data;
}

async function parseJD(jdText: string): Promise<JDJSON> {
  const { data } = await api.post<JDJSON>("/api/parse-jd", {
    job_description_text: jdText,
  });
  return data;
}

async function matchResumeToJD(
  resume: ResumeJSON,
  job: JDJSON,
  resumeText: string = ""
): Promise<MatchReportJSON> {
  const { data } = await api.post<MatchReportJSON>("/api/match", {
    resume,
    job,
    resume_text: resumeText,
  });
  return data;
}

async function getFeedback(
  resume: ResumeJSON,
  job: JDJSON,
  matchReport: MatchReportJSON
): Promise<FeedbackResponse> {
  const { data } = await api.post<FeedbackResponse>("/api/feedback", {
    resume,
    job,
    match_report: matchReport,
  });
  return data;
}

/** Run the full pipeline: parse → match → feedback.
 *  Calls onStep at each stage transition so the UI can show live progress.
 */
export async function analyzeMatch(
  resumeText: string,
  jdText: string,
  onStep: OnStep
): Promise<AnalysisResult> {
  // Step 1 — parse both in parallel (they're independent).
  onStep("parse", "active");
  const [resume, job] = await Promise.all([
    parseResume(resumeText),
    parseJD(jdText),
  ]);
  onStep("parse", "done");

  // Step 2 — deterministic scoring (fast, but still a round-trip).
  onStep("match", "active");
  const match = await matchResumeToJD(resume, job, resumeText);
  onStep("match", "done");

  // Step 3 — LLM feedback (slowest step).
  onStep("feedback", "active");
  const feedback = await getFeedback(resume, job, match);
  onStep("feedback", "done");

  return { match, feedback };
}

/** Download a PDF report for the given analysis result. */
export async function downloadPdfReport(
  match: MatchReportJSON,
  feedback: FeedbackResponse
): Promise<void> {
  const { data } = await api.post(
    "/api/report/pdf",
    { match_report: match, feedback },
    { responseType: "blob" }
  );
  const url = URL.createObjectURL(data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "resume_match_report.pdf";
  a.click();
  URL.revokeObjectURL(url);
}

import { useRef, useState } from "react";
import { uploadResumePdf } from "../api/client";

const SAMPLE_RESUME = `Jane Doe
jane.doe@email.com | (555) 123-4567 | linkedin.com/in/janedoe

SUMMARY
Software engineer with 4 years of experience building scalable web applications using Python, React, and AWS.

SKILLS
Python, TypeScript, React, FastAPI, PostgreSQL, AWS, Docker, Git

EXPERIENCE
Software Engineer — Acme Corp (2021-03 – present)
- Built REST APIs with FastAPI serving 500k+ requests/day
- Reduced CI pipeline time by 40% via parallelised test runs
- Led migration from monolith to microservices architecture

Junior Developer — Startup XYZ (2020-01 – 2021-02)
- Developed React dashboards for internal analytics tools
- Wrote Python ETL scripts processing 10GB+ of daily data

EDUCATION
B.S. Computer Science — State University (2019-05)

CERTIFICATIONS
AWS Certified Developer – Associate`.trim();

function truncateFilename(name: string, max = 28): string {
  if (name.length <= max) return name;
  const ext = name.slice(name.lastIndexOf("."));
  return name.slice(0, max - ext.length - 1) + "…" + ext;
}

interface InputSectionProps {
  resumeText: string;
  jdText: string;
  onResumeChange: (value: string) => void;
  onJDChange: (value: string) => void;
  onAnalyze: () => void;
  onPdfExtracted: (text: string) => void;
  autoAnalyze: boolean;
  onAutoAnalyzeChange: (value: boolean) => void;
  loading: boolean;
}

export default function InputSection({
  resumeText,
  jdText,
  onResumeChange,
  onJDChange,
  onAnalyze,
  onPdfExtracted,
  autoAnalyze,
  onAutoAnalyzeChange,
  loading,
}: InputSectionProps) {
  const canSubmit = resumeText.trim().length > 0 && jdText.trim().length > 0;

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [pdfFilename, setPdfFilename] = useState<string | null>(null);

  async function handlePdfChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setPdfError(null);
    setPdfFilename(file.name);
    setPdfLoading(true);
    try {
      const { resume_text } = await uploadResumePdf(file);
      // Delegate to parent so it can set state + conditionally auto-trigger
      // analysis with the fresh text (avoids stale-closure issues).
      onPdfExtracted(resume_text);
    } catch (err: unknown) {
      setPdfError(err instanceof Error ? err.message : "PDF extraction failed.");
      setPdfFilename(null);
    } finally {
      setPdfLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  function handleClear() {
    onResumeChange("");
    setPdfFilename(null);
    setPdfError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  const showClear = (resumeText.length > 0 || pdfFilename !== null) && !pdfLoading;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Resume */}
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <label
              htmlFor="resume-input"
              className="block text-[11px] font-semibold text-neutral-500 uppercase tracking-widest shrink-0"
            >
              Resume
            </label>

            <div className="flex items-center gap-2 flex-wrap justify-end">
              <button
                type="button"
                onClick={() => { onResumeChange(SAMPLE_RESUME); setPdfFilename(null); setPdfError(null); }}
                disabled={pdfLoading}
                className="text-[11px] text-neutral-500 hover:text-blue-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors duration-150"
              >
                Use sample
              </button>

              <label
                htmlFor="pdf-upload"
                className={
                  "cursor-pointer rounded-lg border border-neutral-700/60 bg-neutral-800/60 px-3 py-1 text-[11px] font-medium text-neutral-400 hover:border-blue-500/50 hover:text-blue-400 focus-within:outline-none focus-within:ring-2 focus-within:ring-blue-500/40 transition-all duration-200 " +
                  (pdfLoading ? "opacity-50 pointer-events-none" : "")
                }
              >
                {pdfLoading ? (
                  <span className="flex items-center gap-1.5">
                    <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Extracting…
                  </span>
                ) : (
                  "Upload PDF"
                )}
                <input
                  ref={fileInputRef}
                  id="pdf-upload"
                  type="file"
                  accept=".pdf,application/pdf"
                  className="sr-only"
                  aria-label="Upload resume PDF"
                  disabled={pdfLoading}
                  onChange={handlePdfChange}
                />
              </label>

              {showClear && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="text-[11px] text-neutral-500 hover:text-red-400 transition-colors duration-150"
                  aria-label="Clear resume"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          {pdfFilename && !pdfError && (
            <p className="text-[11px] text-neutral-500 truncate" title={pdfFilename}>
              {truncateFilename(pdfFilename)}
            </p>
          )}
          {pdfError && (
            <p role="alert" className="text-[11px] text-red-400">
              {pdfError}
            </p>
          )}

          <textarea
            id="resume-input"
            value={resumeText}
            onChange={(e) => onResumeChange(e.target.value)}
            placeholder="Paste resume text here..."
            rows={14}
            className="w-full rounded-xl border border-neutral-700/50 bg-neutral-800/40 px-4 py-3.5 text-sm text-neutral-100 placeholder-neutral-600 shadow-sm focus:border-blue-500/60 focus:ring-2 focus:ring-blue-500/20 focus:shadow-blue-500/5 outline-none resize-y transition-all duration-200"
          />
        </div>

        {/* Job Description */}
        <div className="space-y-2">
          <label
            htmlFor="jd-input"
            className="block text-[11px] font-semibold text-neutral-500 uppercase tracking-widest"
          >
            Job Description
          </label>
          <textarea
            id="jd-input"
            value={jdText}
            onChange={(e) => onJDChange(e.target.value)}
            placeholder="Paste job description text here..."
            rows={14}
            className="w-full rounded-xl border border-neutral-700/50 bg-neutral-800/40 px-4 py-3.5 text-sm text-neutral-100 placeholder-neutral-600 shadow-sm focus:border-blue-500/60 focus:ring-2 focus:ring-blue-500/20 focus:shadow-blue-500/5 outline-none resize-y transition-all duration-200"
          />
        </div>
      </div>

      {/* Analyze row */}
      <div className="flex flex-col items-center gap-3">
        <button
          onClick={onAnalyze}
          disabled={!canSubmit || loading || pdfLoading}
          aria-busy={loading}
          className="px-10 py-3 rounded-xl bg-blue-600 text-white font-semibold text-sm tracking-wide shadow-md shadow-blue-600/20 hover:bg-blue-500 hover:shadow-lg hover:shadow-blue-500/25 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-400 disabled:opacity-35 disabled:shadow-none disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2.5"
        >
          {loading && (
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}
          {loading ? "Analyzing..." : "Analyze Match"}
        </button>

        {/* Auto-analyze checkbox */}
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={autoAnalyze}
            onChange={(e) => onAutoAnalyzeChange(e.target.checked)}
            className="h-3.5 w-3.5 rounded border-neutral-600 bg-neutral-800 text-blue-500 focus:ring-blue-500/40 focus:ring-offset-neutral-950 focus:ring-2"
          />
          <span className="text-[11px] text-neutral-500">Auto-analyze after PDF upload</span>
        </label>
      </div>
    </div>
  );
}

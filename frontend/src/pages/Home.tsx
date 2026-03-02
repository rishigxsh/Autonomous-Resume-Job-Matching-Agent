import { useRef, useState } from "react";
import { analyzeMatch, downloadPdfReport } from "../api/client";
import type { AnalysisResult, StepId, StepStatus } from "../api/client";
import InputSection from "../components/InputSection";
import ScoreCard from "../components/ScoreCard";
import SuggestionsList from "../components/SuggestionsList";
import RewrittenBullets from "../components/RewrittenBullets";
import StepIndicator from "../components/StepIndicator";

const IDLE_STEPS: Record<StepId, StepStatus> = {
  parse: "idle",
  match: "idle",
  feedback: "idle",
};

export default function Home() {
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJDText] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState<Record<StepId, StepStatus>>(IDLE_STEPS);
  const [error, setError] = useState<string | null>(null);
  const [autoAnalyze, setAutoAnalyze] = useState(true);
  const [pdfLoading, setPdfLoading] = useState(false);
  const resultsRef = useRef<HTMLElement>(null);

  function updateStep(step: StepId, status: StepStatus) {
    setSteps((prev) => ({ ...prev, [step]: status }));
  }

  // Called by InputSection after PDF extraction completes.
  // Receives the fresh text directly to avoid stale-closure issues with resumeText state.
  async function handlePdfExtracted(text: string) {
    setResumeText(text);
    if (!autoAnalyze || !jdText.trim() || loading) return;
    await runAnalysis(text, jdText);
  }

  async function handleAnalyze() {
    await runAnalysis(resumeText, jdText);
  }

  async function runAnalysis(resume: string, jd: string) {
    if (loading) return; // prevent double-submit
    setLoading(true);
    setError(null);
    setResult(null);
    setSteps(IDLE_STEPS);

    try {
      const data = await analyzeMatch(resume, jd, updateStep);
      setResult(data);
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Something went wrong. Check that the backend is running.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleDownloadPdf() {
    if (!result || pdfLoading) return;
    setPdfLoading(true);
    try {
      await downloadPdfReport(result.match, result.feedback);
    } catch {
      setError("Failed to download PDF report.");
    } finally {
      setPdfLoading(false);
    }
  }

  const showSteps =
    loading || Object.values(steps).some((s) => s !== "idle");

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-16 space-y-12">
        {/* Header */}
        <header className="text-center space-y-3">
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-neutral-50">
            Resume–Job Matcher
          </h1>
          <p className="text-neutral-500 text-sm max-w-md mx-auto leading-relaxed">
            Paste a resume and a job description. Get an instant match score,
            gap analysis, and AI-rewritten bullets.
          </p>
        </header>

        {/* Input */}
        <InputSection
          resumeText={resumeText}
          jdText={jdText}
          onResumeChange={setResumeText}
          onJDChange={setJDText}
          onAnalyze={handleAnalyze}
          onPdfExtracted={handlePdfExtracted}
          autoAnalyze={autoAnalyze}
          onAutoAnalyzeChange={setAutoAnalyze}
          loading={loading}
        />

        {/* Step progress */}
        {showSteps && !result && <StepIndicator steps={steps} />}

        {/* Error */}
        {error && (
          <div
            role="alert"
            className="animate-fade-in-up rounded-xl border border-red-500/25 bg-red-500/8 px-5 py-3.5 text-sm text-red-400 shadow-sm"
          >
            {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <section ref={resultsRef} className="space-y-10 stagger" aria-label="Analysis results">
            <ScoreCard match={result.match} />

            <div className="flex justify-end">
              <button
                onClick={handleDownloadPdf}
                disabled={pdfLoading}
                aria-label={pdfLoading ? "Generating PDF report" : "Download PDF Report"}
                className="inline-flex items-center gap-2 rounded-lg border border-neutral-700 bg-neutral-800 px-4 py-2 text-sm font-medium text-neutral-200 shadow-sm transition-all hover:bg-neutral-700 hover:border-neutral-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {pdfLoading ? (
                  <>
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                    </svg>
                    Generating…
                  </>
                ) : (
                  <>
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Download PDF Report
                  </>
                )}
              </button>
            </div>

            <SuggestionsList suggestions={result.feedback.suggestions} />
            <RewrittenBullets bullets={result.feedback.rewritten_bullets} />
          </section>
        )}
      </div>
    </div>
  );
}

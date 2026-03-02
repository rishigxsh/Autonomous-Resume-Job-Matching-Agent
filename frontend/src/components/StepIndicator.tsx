import type { StepId, StepStatus } from "../api/client";

interface Step {
  id: StepId;
  label: string;
  sublabel: string;
}

const STEPS: Step[] = [
  {
    id: "parse",
    label: "Parsing documents",
    sublabel: "Resume + job description",
  },
  {
    id: "match",
    label: "Computing match score",
    sublabel: "Deterministic scoring engine",
  },
  {
    id: "feedback",
    label: "Generating feedback",
    sublabel: "AI suggestions + rewritten bullets",
  },
];

interface StepIndicatorProps {
  steps: Record<StepId, StepStatus>;
}

function Spinner() {
  return (
    <svg
      className="animate-spin h-4 w-4 text-blue-400"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle
        className="opacity-20"
        cx="12" cy="12" r="10"
        stroke="currentColor"
        strokeWidth="3"
      />
      <path
        className="opacity-80"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      className="h-4 w-4 text-emerald-400"
      viewBox="0 0 20 20"
      fill="currentColor"
      aria-hidden="true"
    >
      <path
        fillRule="evenodd"
        d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
        clipRule="evenodd"
      />
    </svg>
  );
}

function IdleIcon() {
  return (
    <span className="inline-block h-4 w-4 rounded-full border border-neutral-600" />
  );
}

export default function StepIndicator({ steps }: StepIndicatorProps) {
  return (
    <div
      className="animate-fade-in-up rounded-xl border border-neutral-700/50 bg-neutral-800/40 px-6 py-5 shadow-sm"
      role="status"
      aria-live="polite"
      aria-label="Analysis progress"
    >
      <p className="text-[11px] font-semibold text-neutral-500 uppercase tracking-widest mb-4">
        Analyzing
      </p>
      <ol className="space-y-0 divide-y divide-neutral-700/40">
        {STEPS.map((step) => {
          const status = steps[step.id];
          const isActive = status === "active";
          const isDone = status === "done";

          return (
            <li
              key={step.id}
              className="flex items-center gap-4 py-3 first:pt-0 last:pb-0"
            >
              {/* Icon */}
              <span className="shrink-0 w-5 flex justify-center">
                {isActive ? (
                  <Spinner />
                ) : isDone ? (
                  <CheckIcon />
                ) : (
                  <IdleIcon />
                )}
              </span>

              {/* Labels */}
              <span className="flex flex-col">
                <span
                  className={`text-[13px] font-medium transition-colors duration-300 ${
                    isActive
                      ? "text-neutral-100"
                      : isDone
                        ? "text-neutral-400"
                        : "text-neutral-600"
                  }`}
                >
                  {step.label}
                  {isDone && (
                    <span className="ml-2 text-emerald-500/70 text-[11px] font-normal">
                      done
                    </span>
                  )}
                </span>
                <span className="text-[11px] text-neutral-600 mt-0.5">
                  {step.sublabel}
                </span>
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

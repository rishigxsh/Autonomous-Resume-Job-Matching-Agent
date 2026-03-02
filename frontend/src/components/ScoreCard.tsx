import type { MatchReportJSON } from "../types/api";

interface ScoreCardProps {
  match: MatchReportJSON;
}

/* --- Color helpers with updated 80/60 thresholds --- */

function strokeColor(score: number): string {
  if (score >= 80) return "#34d399";  // emerald-400
  if (score >= 60) return "#fbbf24";  // amber-400
  return "#f87171";                    // red-400
}

function textColor(score: number): string {
  if (score >= 80) return "text-emerald-400";
  if (score >= 60) return "text-amber-400";
  return "text-red-400";
}

function barFill(score: number): string {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 60) return "bg-amber-500";
  return "bg-red-500";
}

function ringBg(score: number): string {
  if (score >= 80) return "shadow-emerald-500/8";
  if (score >= 60) return "shadow-amber-500/8";
  return "shadow-red-500/8";
}

/* --- Circular score ring --- */

function ScoreRing({ score }: { score: number }) {
  const radius = 45;
  const circumference = 2 * Math.PI * radius; // ≈ 283
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="140" height="140" viewBox="0 0 100 100" className="-rotate-90">
        {/* Track */}
        <circle
          cx="50" cy="50" r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="6"
          className="text-neutral-800"
        />
        {/* Fill */}
        <circle
          cx="50" cy="50" r={radius}
          fill="none"
          stroke={strokeColor(score)}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="score-ring-animated"
          style={{ strokeDashoffset: offset } as React.CSSProperties}
        />
      </svg>
      {/* Number overlay */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-4xl font-bold tabular-nums ${textColor(score)}`}>
          {score}
        </span>
        <span className="text-xs text-neutral-500 -mt-0.5">/ 100</span>
      </div>
    </div>
  );
}

/* --- Progress bar for component scores --- */

function Bar({ score }: { score: number }) {
  return (
    <div className="h-1.5 rounded-full bg-neutral-700/60 mt-2">
      <div
        className={`h-full rounded-full ${barFill(score)} transition-all duration-700 ease-out`}
        style={{ width: `${score}%` }}
      />
    </div>
  );
}

const LABELS: Record<string, string> = {
  required_skills_score: "Required Skills",
  preferred_skills_score: "Preferred Skills",
  experience_score: "Experience",
  responsibilities_score: "Responsibilities",
  education_score: "Education",
};

const WEIGHTS: Record<string, number> = {
  required_skills_score: 35,
  preferred_skills_score: 15,
  experience_score: 25,
  responsibilities_score: 15,
  education_score: 10,
};

/* --- Main component --- */

export default function ScoreCard({ match }: ScoreCardProps) {
  const cs = match.component_scores;

  return (
    <div className="space-y-8 stagger">
      {/* Overall score */}
      <div
        className={`flex flex-col items-center justify-center rounded-2xl border border-neutral-700/50 bg-neutral-800/40 p-10 shadow-lg ${ringBg(match.overall_score)}`}
      >
        <p className="text-[11px] font-semibold text-neutral-500 uppercase tracking-widest mb-4">
          Overall Match
        </p>
        <ScoreRing score={match.overall_score} />
        <p className="text-neutral-400 text-[13px] text-center mt-6 max-w-lg leading-relaxed">
          {match.rationale}
        </p>
      </div>

      {/* Component breakdown */}
      <div>
        <h3 className="text-[11px] font-semibold text-neutral-500 uppercase tracking-widest mb-4">
          Score Breakdown
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {Object.entries(cs).map(([key, value]) => (
            <div
              key={key}
              className="rounded-xl border border-neutral-700/50 bg-neutral-800/40 p-4 shadow-sm hover:shadow-md hover:border-neutral-600/60 transition-all duration-200"
            >
              <p className="text-[11px] text-neutral-500 font-medium">
                {LABELS[key] ?? key}
              </p>
              <div className="flex items-baseline justify-between mt-1">
                <span className={`text-xl font-bold tabular-nums ${textColor(value)}`}>
                  {value}
                </span>
                <span className="text-[10px] text-neutral-600 font-medium">
                  w{WEIGHTS[key]}
                </span>
              </div>
              <Bar score={value} />
            </div>
          ))}
        </div>
      </div>

      {/* Skills */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl border border-neutral-700/50 bg-neutral-800/40 p-5 shadow-sm">
          <h3 className="text-[11px] font-semibold text-neutral-500 uppercase tracking-widest mb-3">
            Matched Skills
          </h3>
          <div className="flex flex-col gap-3">
            {match.matched_skills.length > 0 ? (
              match.matched_skills.map((s) => (
                <div key={s.skill}>
                  <span className="inline-block px-2.5 py-1 text-xs font-medium rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {s.skill}
                  </span>
                  {s.evidence.length > 0 && (
                    <ul className="mt-1.5 ml-3 space-y-0.5">
                      {s.evidence.map((snippet, i) => (
                        <li key={i} className="text-[11px] text-neutral-400 leading-relaxed">
                          <span className="text-neutral-600 mr-1">&bull;</span>
                          {snippet}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))
            ) : (
              <span className="text-sm text-neutral-500">None</span>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-neutral-700/50 bg-neutral-800/40 p-5 shadow-sm">
          <h3 className="text-[11px] font-semibold text-neutral-500 uppercase tracking-widest mb-3">
            Missing Skills
          </h3>
          <div className="flex flex-col gap-3">
            {match.missing_skills.length > 0 ? (
              match.missing_skills.map((s) => (
                <div key={s.skill}>
                  <span className="inline-block px-2.5 py-1 text-xs font-medium rounded-md bg-red-500/10 text-red-400 border border-red-500/20">
                    {s.skill}
                  </span>
                  <p className="mt-1 ml-3 text-[11px] text-neutral-600 italic">
                    No direct evidence found
                  </p>
                </div>
              ))
            ) : (
              <span className="text-sm text-emerald-500/70">All required skills matched</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

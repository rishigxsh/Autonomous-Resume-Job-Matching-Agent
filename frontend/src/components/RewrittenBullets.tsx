interface RewrittenBulletsProps {
  bullets: string[];
}

export default function RewrittenBullets({ bullets }: RewrittenBulletsProps) {
  if (bullets.length === 0) return null;

  return (
    <div>
      <h3 className="text-[11px] font-semibold text-neutral-500 uppercase tracking-widest mb-4">
        Rewritten Resume Bullets
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {bullets.map((b, i) => (
          <div
            key={i}
            className="group rounded-xl border border-neutral-700/50 bg-neutral-800/40 p-5 shadow-sm hover:shadow-md hover:border-neutral-600/60 transition-all duration-200"
          >
            <div className="flex gap-3">
              <span className="text-emerald-500/60 text-lg leading-none mt-0.5 shrink-0">
                &bull;
              </span>
              <p className="text-[13px] text-neutral-300 leading-relaxed">
                {b}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

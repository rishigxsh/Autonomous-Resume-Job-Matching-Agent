interface SuggestionsListProps {
  suggestions: string[];
}

export default function SuggestionsList({ suggestions }: SuggestionsListProps) {
  if (suggestions.length === 0) return null;

  return (
    <div className="rounded-2xl border border-neutral-700/50 bg-neutral-800/40 p-6 shadow-sm">
      <h3 className="text-[11px] font-semibold text-neutral-500 uppercase tracking-widest mb-5">
        Suggestions
      </h3>
      <ul className="space-y-0 divide-y divide-neutral-700/40">
        {suggestions.map((s, i) => (
          <li
            key={i}
            className="flex gap-3 py-3 first:pt-0 last:pb-0 text-[13px] text-neutral-300 leading-snug"
          >
            <span className="inline-flex items-center justify-center h-5 w-5 shrink-0 rounded-full bg-blue-500/10 text-blue-400 text-[10px] font-bold mt-px">
              {i + 1}
            </span>
            <span>{s}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

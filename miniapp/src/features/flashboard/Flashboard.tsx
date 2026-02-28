type Props = { calledNumbers: number[] }

export function Flashboard({ calledNumbers }: Props) {
  const set = new Set(calledNumbers)
  const columns = [
    { letter: 'B', start: 1 },
    { letter: 'I', start: 16 },
    { letter: 'N', start: 31 },
    { letter: 'G', start: 46 },
    { letter: 'O', start: 61 },
  ]

  return (
    <section className="rounded-xl border border-slate-700 bg-slate-950 p-2">
      <table className="w-full table-fixed border-collapse text-center">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.letter} className="border border-slate-700 bg-slate-800 py-1 text-xs tracking-widest text-amber-300">
                {col.letter}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 15 }, (_, rowIdx) => (
            <tr key={rowIdx}>
              {columns.map((col) => {
                const n = col.start + rowIdx
                return (
                  <td
                    key={`${col.letter}-${n}`}
                    className={`border border-slate-700 py-[2px] text-[11px] font-semibold ${
                      set.has(n) ? 'bg-amber-500 text-slate-900' : 'bg-slate-900 text-slate-200'
                    }`}
                  >
                    {n}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

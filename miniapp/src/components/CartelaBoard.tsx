import type { Cartela } from '../types/bingo'

type Props = {
  cartela: Cartela
  markedNumbers?: number[]
  onNumberClick?: (n: number) => void
  compact?: boolean
}

const HEADERS = ['B', 'I', 'N', 'G', 'O']

export function CartelaBoard({ cartela, markedNumbers = [], onNumberClick, compact = false }: Props) {
  const marked = new Set(markedNumbers)

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-700 bg-slate-900">
      <div className="grid grid-cols-5 bg-slate-800">
        {HEADERS.map((h) => (
          <div key={h} className={`text-center font-bold tracking-widest text-amber-300 ${compact ? 'py-0.5 text-[10px]' : 'py-1 text-sm'}`}>
            {h}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-5 gap-px bg-slate-700 p-px">
        {cartela.numbers.flat().map((n, i) => {
          const isFree = n === 'FREE'
          const isMarked = typeof n === 'number' && marked.has(n)
          const canClick = !!onNumberClick

          return (
            <button
              key={`${n}-${i}`}
              type="button"
              onClick={() => {
                if (typeof n === 'number') onNumberClick?.(n)
              }}
              disabled={!canClick || isFree}
              className={`aspect-square bg-slate-950 font-semibold transition ${compact ? 'text-[9px]' : 'text-[11px]'} ${
                isFree
                  ? 'bg-emerald-700 text-emerald-100'
                  : isMarked
                  ? '!bg-green-500 text-white'
                  : 'bg-slate-900 text-slate-300'
              } ${canClick ? 'hover:bg-slate-800' : ''}`}
            >
              {n}
            </button>
          )
        })}
      </div>
    </section>
  )
}

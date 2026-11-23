// How the board says a length of time, as lem_board_model.span and ago say it on the server.
export function span (ms) {
  const s = Math.max(0, Math.round(ms / 1000))
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  if (m < 10) return `${m}m ${String(s % 60).padStart(2, '0')}s`
  if (m < 60) return `${m}m`
  const hours = Math.floor(m / 60)
  return hours < 48 ? `${hours}h ${String(m % 60).padStart(2, '0')}m` : `${Math.floor(hours / 24)}d ${hours % 24}h`
}
export const ago = ms => (ms < 5000 ? 'just now' : `${span(ms)} ago`)
// A clock time to the second, with its date when it is not on the day of `day` (lem_board_model.hms).
const dayKey = ms => new Date(ms).toDateString()
export const hms = (ms, day = Date.now()) => (dayKey(ms) === dayKey(day) ? '' : `${new Date(ms).toLocaleDateString([], { day: 'numeric', month: 'short' })} `) +
  new Date(ms).toLocaleTimeString([], { hourCycle: 'h23', hour: '2-digit', minute: '2-digit', second: '2-digit' })

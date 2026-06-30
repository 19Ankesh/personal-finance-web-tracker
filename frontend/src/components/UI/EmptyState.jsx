export default function EmptyState({ icon = '📭', message = 'No data found', subtitle }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center animate-fade-in">
      <div className="w-16 h-16 rounded-2xl bg-surface-700 flex items-center justify-center text-3xl mb-4">
        {icon}
      </div>
      <p className="text-slate-300 font-medium">{message}</p>
      {subtitle && <p className="text-slate-500 text-sm mt-1 max-w-xs">{subtitle}</p>}
    </div>
  )
}

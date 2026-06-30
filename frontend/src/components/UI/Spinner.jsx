export default function Spinner({ size = 'md', className = '' }) {
  const sizes = { sm: 'w-5 h-5 border-2', md: 'w-8 h-8 border-2', lg: 'w-12 h-12 border-[3px]' }
  return (
    <div className={`flex items-center justify-center ${className}`}>
      <div className={`${sizes[size]} border-surface-600 border-t-indigo-500 rounded-full animate-spin`} />
    </div>
  )
}

export function PageSpinner() {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4">
      <div className="w-12 h-12 border-[3px] border-surface-700 border-t-indigo-500 rounded-full animate-spin" />
      <p className="text-slate-400 text-sm animate-pulse">Loading...</p>
    </div>
  )
}

export default function ErrorState({ message = 'Something went wrong', onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center animate-fade-in">
      <div className="w-16 h-16 rounded-2xl bg-red-500/10 flex items-center justify-center text-3xl mb-4">
        ⚠️
      </div>
      <p className="text-red-400 font-medium">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-4 btn-secondary text-sm">
          Try Again
        </button>
      )}
    </div>
  )
}

export function SkeletonCard() {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 animate-pulse">
      {/* Title */}
      <div className="h-6 bg-gray-200 rounded w-3/4 mb-3"></div>

      {/* Company */}
      <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>

      {/* Tags */}
      <div className="flex gap-2 mb-4">
        <div className="h-6 bg-gray-200 rounded w-16"></div>
        <div className="h-6 bg-gray-200 rounded w-20"></div>
        <div className="h-6 bg-gray-200 rounded w-24"></div>
      </div>

      {/* Description */}
      <div className="space-y-2 mb-4">
        <div className="h-4 bg-gray-200 rounded w-full"></div>
        <div className="h-4 bg-gray-200 rounded w-5/6"></div>
      </div>

      {/* Footer */}
      <div className="flex justify-between items-center">
        <div className="h-4 bg-gray-200 rounded w-24"></div>
        <div className="h-8 bg-gray-200 rounded w-32"></div>
      </div>
    </div>
  )
}

interface SkeletonListProps {
  count?: number
}

export function SkeletonList({ count = 3 }: SkeletonListProps) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  )
}

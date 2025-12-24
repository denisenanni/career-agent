import { useState } from 'react'
import { ChevronRight } from 'lucide-react'

interface CollapsibleSectionProps {
  title: string
  selectedCount?: number
  children: React.ReactNode
  defaultOpen?: boolean
}

export function CollapsibleSection({
  title,
  selectedCount,
  children,
  defaultOpen = false,
}: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full text-left py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
      >
        <span className="flex items-center gap-2">
          <ChevronRight
            className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-90' : ''}`}
          />
          {title}
        </span>
        {selectedCount !== undefined && selectedCount > 0 && (
          <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">
            {selectedCount} selected
          </span>
        )}
      </button>
      {isOpen && <div className="pl-6 pb-2">{children}</div>}
    </div>
  )
}

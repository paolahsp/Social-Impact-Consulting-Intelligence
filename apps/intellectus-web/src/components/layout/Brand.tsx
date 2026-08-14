interface BrandProps {
  compact?: boolean
}

export function Brand({ compact = false }: BrandProps) {
  return (
    <div className="min-w-0">
      <p
        className={`font-serif font-semibold leading-none text-ink ${compact ? 'text-xl' : 'text-2xl'}`}
      >
        Intellectus
      </p>
      <p className="mt-1 truncate text-xs text-muted">
        Social Impact Intelligence
      </p>
    </div>
  )
}

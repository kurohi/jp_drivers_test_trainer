import { useState, useMemo, useCallback } from "react"

interface TrajectoryPoint {
  x: number
  y: number
}

interface TrajectoryData {
  path: TrajectoryPoint[]
  failure_reason_en?: string
  failure_reason_pt?: string
}

interface TrajectoryPlayerProps {
  trajectoryJson: string
  color: string
  failureReason?: string
  isWrong?: boolean
}

export function TrajectoryPlayer({
  trajectoryJson,
  color,
  failureReason,
  isWrong = false,
}: TrajectoryPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [playKey, setPlayKey] = useState(0)

  const data = useMemo<TrajectoryData | null>(() => {
    try {
      return JSON.parse(trajectoryJson) as TrajectoryData
    } catch {
      return null
    }
  }, [trajectoryJson])

  const svgPathD = useMemo(() => {
    if (!data?.path?.length) return ""
    const pts = data.path
    let d = `M ${pts[0].x} ${pts[0].y}`
    for (let i = 1; i < pts.length; i++) {
      d += ` L ${pts[i].x} ${pts[i].y}`
    }
    return d
  }, [data])

  const totalDuration = useMemo(() => {
    if (!data?.path?.length) return 0
    return Math.max(1, data.path.length - 1) * 1.5
  }, [data])

  const handlePlay = useCallback(() => {
    setIsPlaying(true)
    setPlayKey((k) => k + 1)
    setTimeout(() => setIsPlaying(false), totalDuration * 1000)
  }, [totalDuration])

  if (!data) return null

  return (
    <div data-testid="trajectory-player">
      <div className="relative">
        <svg
          viewBox="0 0 500 500"
          className="w-full max-w-md mx-auto"
          data-testid="trajectory-svg"
        >
          <path
            d={svgPathD}
            fill="none"
            stroke={color}
            strokeWidth="2"
            strokeDasharray="4,4"
            opacity="0.4"
          />

          <circle
            cx={data.path[0].x}
            cy={data.path[0].y}
            r="6"
            fill={color}
            opacity="0.5"
          />

          <circle
            cx={data.path[data.path.length - 1].x}
            cy={data.path[data.path.length - 1].y}
            r="6"
            fill={color}
            opacity="0.5"
          />

          {isPlaying && (
            <circle
              key={playKey}
              r="8"
              fill={color}
              stroke="white"
              strokeWidth="2"
            >
              <animateMotion
                dur={`${totalDuration}s`}
                repeatCount="1"
                fill="freeze"
                path={svgPathD}
              />
            </circle>
          )}
        </svg>

        <button
          onClick={handlePlay}
          disabled={isPlaying}
          data-testid="play-trajectory"
          className="mt-2 inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground shadow transition-colors hover:bg-primary/90 disabled:opacity-50"
        >
          {isPlaying ? (
            <span className="animate-pulse">Playback...</span>
          ) : (
            <>
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <polygon points="5,3 19,12 5,21" />
              </svg>
              Play trajectory
            </>
          )}
        </button>
      </div>

      {isWrong && failureReason && (
        <div
          className="mt-3 rounded-md border border-destructive/50 bg-destructive/10 p-3"
          data-testid="failure-reason"
        >
          <p className="text-xs font-semibold text-destructive">
            {failureReason}
          </p>
        </div>
      )}
    </div>
  )
}

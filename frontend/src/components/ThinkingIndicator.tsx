import { useEffect, useState } from 'react'
import './ThinkingIndicator.css'

const STEPS = [
  'Analyzing your requirements…',
  'Planning test cases…',
  'Drafting test data…',
  'Reviewing automation options…',
  'Assessing release risks…',
  'Still working — local models can take a minute…',
]

type ThinkingIndicatorProps = {
  startedAt: number
}

export function ThinkingIndicator({ startedAt }: ThinkingIndicatorProps) {
  const [stepIndex, setStepIndex] = useState(0)
  const [elapsedSec, setElapsedSec] = useState(0)

  useEffect(() => {
    const stepTimer = window.setInterval(() => {
      setStepIndex((current) => (current + 1) % STEPS.length)
    }, 4000)

    const elapsedTimer = window.setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - startedAt) / 1000))
    }, 1000)

    return () => {
      window.clearInterval(stepTimer)
      window.clearInterval(elapsedTimer)
    }
  }, [startedAt])

  return (
    <div className="thinking-indicator" role="status" aria-live="polite">
      <div className="thinking-dots" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <p className="thinking-message">{STEPS[stepIndex]}</p>
      <p className="thinking-elapsed muted">
        {elapsedSec < 15
          ? 'Generating quality assistance…'
          : `Still processing (${elapsedSec}s) — please wait`}
      </p>
    </div>
  )
}

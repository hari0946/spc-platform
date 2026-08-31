import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  /** Meaningful, stage-specific message -- never a bare generic spinner.
   * e.g. "Uploading CSV...", "Running SPC analysis...", "Comparing with baseline..." */
  message: string;
  className?: string;
}

export function LoadingState({ message, className }: LoadingStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 py-16 text-center ${className ?? ""}`} role="status" aria-live="polite">
      <Loader2 className="h-8 w-8 animate-spin text-brand-600" aria-hidden="true" />
      <p className="text-sm font-medium text-ink-700">{message}</p>
    </div>
  );
}

interface StepProgressProps {
  steps: string[];
  currentStepIndex: number;
}

/** For multi-stage backend workflows (upload -> bronze -> validate ->
 * silver), shows which stage is active rather than one undifferentiated
 * spinner. */
export function StepProgress({ steps, currentStepIndex }: StepProgressProps) {
  return (
    <div className="flex flex-col items-center gap-4 py-16" role="status" aria-live="polite">
      <Loader2 className="h-8 w-8 animate-spin text-brand-600" aria-hidden="true" />
      <ol className="flex flex-col gap-1.5 text-sm">
        {steps.map((step, index) => (
          <li
            key={step}
            className={
              index < currentStepIndex
                ? "text-status-normal"
                : index === currentStepIndex
                  ? "font-semibold text-ink-900"
                  : "text-ink-400"
            }
          >
            {step}
          </li>
        ))}
      </ol>
    </div>
  );
}

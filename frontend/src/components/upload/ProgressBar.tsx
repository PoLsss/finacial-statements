/**
 * ProgressBar Component - Upload/Processing Progress
 */

'use client';

import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface ProgressBarProps {
  progress: number;
  currentStep: string;
  status: 'idle' | 'uploading' | 'processing' | 'success' | 'error';
}

const steps = [
  'Uploading file...',
  'Parsing PDF with Landing AI...',
  'Cleaning markdown...',
  'Creating chunks...',
  'Generating embeddings...',
  'Storing in database...',
  'Complete!',
];

export function ProgressBar({ progress, currentStep, status }: ProgressBarProps) {
  if (status === 'idle') return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Processing Status</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Step indicators */}
        <div className="space-y-2">
          {steps.map((step, index) => {
            const stepProgress = ((index + 1) / steps.length) * 100;
            const isComplete = progress >= stepProgress;
            const isCurrent = currentStep.includes(step.replace('...', ''));
            
            return (
              <div key={step} className="flex items-center gap-3">
                <span className="text-lg">
                  {isComplete ? '✅' : isCurrent ? '⏳' : '○'}
                </span>
                <span
                  className={`text-sm ${
                    isComplete
                      ? 'text-green-600'
                      : isCurrent
                      ? 'text-primary font-medium'
                      : 'text-muted-foreground'
                  }`}
                >
                  {step}
                </span>
                {isCurrent && status === 'processing' && (
                  <span className="text-xs text-muted-foreground ml-auto">Processing</span>
                )}
                {isComplete && (
                  <span className="text-xs text-green-600 ml-auto">Done</span>
                )}
              </div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div className="space-y-2">
          <Progress value={progress} className="h-2" />
          <p className="text-sm text-muted-foreground text-center">{progress}%</p>
        </div>

        {/* Status indicator */}
        {status === 'error' && (
          <div className="bg-destructive/10 text-destructive px-4 py-2 rounded-md text-sm">
            An error occurred during processing
          </div>
        )}
        
        {status === 'success' && (
          <div className="bg-green-500/10 text-green-600 px-4 py-2 rounded-md text-sm">
            ✅ Processing completed successfully!
          </div>
        )}
      </CardContent>
    </Card>
  );
}

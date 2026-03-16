/**
 * useUpload Hook - Handles PDF upload logic with step-driven progress
 */

import { useCallback, useRef } from 'react';
import { useUploadStore } from '@/stores/uploadStore';
import { uploadPDF } from '@/lib/api';

// Step progress milestones (must match PROCESS_STEPS order in UploadContainer)
const STEP_MILESTONES = [5, 15, 30, 55, 75, 90, 100];

export function useUpload() {
  const {
    status,
    progress,
    currentStep,
    result,
    error,
    file,
    setFile,
    setStatus,
    setProgress,
    setCurrentStep,
    setResult,
    setError,
    reset,
  } = useUploadStore();

  const progressTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopProgressTimer = () => {
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
    }
  };

  const upload = useCallback(
    async (resetDatabase: boolean = false, chunkSize: number = 1000) => {
      if (!file) {
        setError('No file selected');
        return;
      }

      setStatus('uploading');
      setProgress(0);
      setCurrentStep('Đang tải file lên...');
      setError(null);

      // Drive progress through steps automatically
      // Each step gets a time slot; final step waits for real completion
      let stepIdx = 0;
      const driveProgress = () => {
        if (stepIdx < STEP_MILESTONES.length - 1) {
          // advance to next milestone but stop at 90 until real response
          setProgress(STEP_MILESTONES[stepIdx]);
          stepIdx++;
        }
      };

      // Advance through first 6 steps over ~8s (1.3s each)
      progressTimerRef.current = setInterval(driveProgress, 1300);

      try {
        const response = await uploadPDF(file, resetDatabase, chunkSize);
        stopProgressTimer();

        if (response.success && response.data) {
          setProgress(100);
          setCurrentStep('Hoàn thành!');
          setStatus('success');
          setResult(response.data);
        } else {
          setError(response.error || 'Tải lên thất bại');
          setStatus('error');
        }
      } catch (err) {
        stopProgressTimer();
        const errorMessage = err instanceof Error ? err.message : 'Tải lên thất bại';
        setError(errorMessage);
        setStatus('error');
      }
    },
    [file, setStatus, setProgress, setCurrentStep, setError, setResult]
  );

  const selectFile = useCallback(
    (selectedFile: File) => {
      setFile(selectedFile);
      setError(null);
      setStatus('idle');
      setResult(null);
    },
    [setFile, setError, setStatus, setResult]
  );

  return {
    status,
    progress,
    currentStep,
    result,
    error,
    file,
    selectFile,
    upload,
    reset,
  };
}

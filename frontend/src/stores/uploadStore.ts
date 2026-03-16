/**
 * Upload Store - Zustand
 */

import { create } from 'zustand';
import type { UploadData } from '@/types/api';

type UploadStatus = 'idle' | 'uploading' | 'processing' | 'success' | 'error';

interface UploadState {
  status: UploadStatus;
  progress: number;
  currentStep: string;
  result: UploadData | null;
  error: string | null;
  file: File | null;

  // Actions
  setFile: (file: File | null) => void;
  setStatus: (status: UploadStatus) => void;
  setProgress: (progress: number) => void;
  setCurrentStep: (step: string) => void;
  setResult: (result: UploadData | null) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useUploadStore = create<UploadState>((set) => ({
  status: 'idle',
  progress: 0,
  currentStep: '',
  result: null,
  error: null,
  file: null,

  setFile: (file) => set({ file }),

  setStatus: (status) => set({ status }),

  setProgress: (progress) => set({ progress }),

  setCurrentStep: (step) => set({ currentStep: step }),

  setResult: (result) => set({ result }),

  setError: (error) => set({ error, status: error ? 'error' : 'idle' }),

  reset: () =>
    set({
      status: 'idle',
      progress: 0,
      currentStep: '',
      result: null,
      error: null,
      file: null,
    }),
}));

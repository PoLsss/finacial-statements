/**
 * DropZone Component - Drag & Drop PDF Upload
 */

'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent } from '@/components/ui/card';

interface DropZoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
  currentFile?: File | null;
  compact?: boolean;
}

export function DropZone({ onFileSelect, disabled, currentFile, compact }: DropZoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    disabled,
  });

  return (
    <Card
      {...getRootProps()}
      className={`
        cursor-pointer border-2 border-dashed transition-colors
        ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary/50'}
      `}
    >
      <CardContent className={`flex flex-col items-center justify-center ${compact ? 'py-3' : 'py-12'}`}>
        <input {...getInputProps()} />
        
        <div className={`${compact ? 'text-2xl mb-1.5' : 'text-5xl mb-4'}`}>📄</div>
        
        {currentFile ? (
          <div className="text-center">
            <p className={`font-medium text-foreground ${compact ? 'text-sm' : 'text-lg'}`}>{currentFile.name}</p>
            <p className="text-xs text-muted-foreground mt-1">
              {(currentFile.size / 1024 / 1024).toFixed(2)} MB
            </p>
            <p className="text-xs text-primary mt-1.5">Nhấn hoặc kéo thả để thay thế</p>
          </div>
        ) : isDragActive ? (
          <p className={`text-primary ${compact ? 'text-sm' : 'text-lg'}`}>Thả file PDF vào đây...</p>
        ) : (
          <div className="text-center">
            <p className={`font-medium ${compact ? 'text-sm' : 'text-lg'}`}>Kéo &amp; Thả file PDF vào đây</p>
            <p className="text-xs text-muted-foreground mt-1">hoặc nhấn để chọn file</p>
            <p className="text-xs text-muted-foreground mt-2">Hỗ trợ: .pdf (tối đa 50MB)</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

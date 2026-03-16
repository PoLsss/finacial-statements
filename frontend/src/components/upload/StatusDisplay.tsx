/**
 * StatusDisplay Component - Shows processing results
 */

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { UploadData } from '@/types/api';

interface StatusDisplayProps {
  result: UploadData | null;
  error: string | null;
}

export function StatusDisplay({ result, error }: StatusDisplayProps) {
  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg text-destructive flex items-center gap-2">
            ❌ Error
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!result) return null;

  return (
    <Card className="border-green-500">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg text-green-600 flex items-center gap-2">
          ✅ Processing Complete
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Source</p>
            <p className="font-medium">{result.source_name}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Processing Time</p>
            <p className="font-medium">{result.processing_time_seconds}s</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary">
            � {result.total_chunks} chunks
          </Badge>
          <Badge variant="secondary">
            🔢 {result.total_embeddings} embeddings
          </Badge>
          {result.extraction_method && (
            <Badge variant="secondary">
              🔍 {result.extraction_method}
            </Badge>
          )}
          <Badge variant={result.ratios_computed ? 'default' : 'outline'}>
            {result.ratios_computed ? '✅ Ratios computed' : 'Ratios not computed'}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

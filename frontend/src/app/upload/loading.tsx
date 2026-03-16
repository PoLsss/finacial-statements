/**
 * Upload Loading State
 */

export default function UploadLoading() {
  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-pulse">
      <div className="text-center">
        <div className="h-9 bg-muted rounded w-64 mx-auto"></div>
        <div className="h-5 bg-muted rounded w-48 mx-auto mt-2"></div>
      </div>
      
      <div className="border-2 border-dashed border-muted rounded-lg h-48"></div>
      
      <div className="border rounded-lg p-6">
        <div className="h-6 bg-muted rounded w-24 mb-4"></div>
        <div className="space-y-3">
          <div className="h-4 bg-muted rounded w-48"></div>
          <div className="h-4 bg-muted rounded w-36"></div>
        </div>
      </div>
    </div>
  );
}

/**
 * Chat Loading State
 */

export default function ChatLoading() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="text-center">
        <div className="h-9 bg-muted rounded w-80 mx-auto"></div>
        <div className="h-5 bg-muted rounded w-64 mx-auto mt-2"></div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="border rounded-lg p-6">
            <div className="h-6 bg-muted rounded w-32 mb-4"></div>
            <div className="h-[500px] bg-muted/50 rounded"></div>
            <div className="h-16 bg-muted rounded mt-4"></div>
          </div>
        </div>
        
        <div>
          <div className="border rounded-lg p-6 space-y-4">
            <div className="h-6 bg-muted rounded w-40"></div>
            <div className="h-32 bg-muted/50 rounded"></div>
          </div>
        </div>
      </div>
    </div>
  );
}

import { Smile } from "lucide-react";

export default function SdkDocsPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-8 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-teal-50">
        <Smile className="h-8 w-8 text-teal-700" strokeWidth={1.75} />
      </div>
      <p className="mt-6 text-lg font-medium text-heading">SDK docs are still in the works</p>
      <p className="mt-2 text-sm text-muted">Check back soon.</p>
    </div>
  );
}

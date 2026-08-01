import { Sidebar } from "@/components/docs/Sidebar";
import { getAllModels } from "@/lib/models";

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  const models = getAllModels();

  return (
    <div className="flex min-h-screen">
      <Sidebar models={models} />
      <main className="min-w-0 flex-1">{children}</main>
    </div>
  );
}

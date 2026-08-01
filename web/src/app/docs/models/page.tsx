import { ModelCard } from "@/components/docs/ModelCard";
import { getAllModels } from "@/lib/models";

export default function ModelsPage() {
  const models = getAllModels();

  return (
    <div className="mx-auto max-w-5xl px-8 py-16 sm:px-12">
      <div className="max-w-2xl">
        <h1 className="text-2xl font-semibold text-heading">Models</h1>
        <p className="mt-3 text-base text-body">
          This page lists every VLA model Argos supports or is evaluating, with what&apos;s
          needed to run each one and how it performs on real hardware.
        </p>
      </div>

      <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {models.map((model) => (
          <ModelCard key={model.slug} model={model} />
        ))}
      </div>
    </div>
  );
}

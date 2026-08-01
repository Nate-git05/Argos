import { notFound } from "next/navigation";
import { ModelDetail } from "@/components/docs/ModelDetail";
import { getAllModels, getModelBySlug } from "@/lib/models";

export function generateStaticParams() {
  return getAllModels().map((m) => ({ slug: m.slug }));
}

export default async function ModelDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const model = getModelBySlug(slug);

  if (!model) notFound();

  return <ModelDetail model={model} />;
}

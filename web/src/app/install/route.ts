const SCRIPT_URL = "https://raw.githubusercontent.com/Nate-git05/Argos/main/install/install.sh";

export async function GET() {
  const res = await fetch(SCRIPT_URL, { next: { revalidate: 300 } });

  if (!res.ok) {
    return new Response("failed to fetch install script", { status: 502 });
  }

  const script = await res.text();

  return new Response(script, {
    headers: {
      "Content-Type": "text/x-shellscript; charset=utf-8",
      "Cache-Control": "public, max-age=300",
    },
  });
}

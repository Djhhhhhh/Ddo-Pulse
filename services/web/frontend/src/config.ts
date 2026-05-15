/** Runtime config from API (backed by ~/.ddo_pulse/web.yaml). */

export type WebAppConfig = {
  title: string;
  api_base: string;
  api_host: string;
  api_port: number;
};

const fallback: WebAppConfig = {
  title: "Ddo-Pulse",
  api_base: "/api",
  api_host: "127.0.0.1",
  api_port: 8765,
};

let cached: WebAppConfig | null = null;

export async function loadAppConfig(): Promise<WebAppConfig> {
  if (cached) return cached;
  try {
    const res = await fetch("/api/web-config");
    if (res.ok) {
      cached = (await res.json()) as WebAppConfig;
      return cached;
    }
  } catch {
    /* use fallback when API offline */
  }
  cached = fallback;
  return cached;
}

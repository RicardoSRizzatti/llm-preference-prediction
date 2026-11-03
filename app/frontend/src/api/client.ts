// Único ponto de acesso à API. Componentes não chamam fetch diretamente.
import type { FeatureValues, ModelInfo, Prediction } from "./types";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

function errorDetail(body: unknown, fallback: string): string {
  if (!body || typeof body !== "object" || !("detail" in body)) return fallback;
  const detail = (body as { detail: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => (typeof d === "string" ? d : (d as { msg?: string }).msg ?? JSON.stringify(d)))
      .join("; ");
  }
  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    throw new ApiError(response.status, errorDetail(body, response.statusText));
  }
  return (await response.json()) as T;
}

export const api = {
  model: () => request<ModelInfo>("/model"),

  predict: (features: FeatureValues, signal?: AbortSignal) =>
    request<Prediction>("/predict", { method: "POST", body: JSON.stringify({ features }), signal }),

  predictBatch: (instances: FeatureValues[], signal?: AbortSignal) =>
    request<{ predictions: Prediction[] }>("/predict/batch", {
      method: "POST",
      body: JSON.stringify({ instances }),
      signal,
    }),
};

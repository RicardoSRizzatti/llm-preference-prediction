// Análise de sensibilidade: varia uma feature e mantém as demais fixas nos valores atuais.
import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import type { FeatureValues, ModelInfo } from "../api/types";
import { LineChart, type LineSeries } from "../charts";
import { displayName, formatDecimal, formatPercent } from "../utils/format";
import { useDebounced } from "../utils/useDebounced";

const POINTS = 80;

interface SensitivityPanelProps {
  model: ModelInfo;
  values: FeatureValues;
  feature: string;
}

export function SensitivityPanel({ model, values, feature }: SensitivityPanelProps) {
  const [series, setSeries] = useState<LineSeries[]>([]);
  const [error, setError] = useState<string | null>(null);
  const debouncedValues = useDebounced(values, 250);
  const rawStats = model.feature_stats[feature];
  const stats = rawStats?.type === "numeric" ? rawStats : undefined;
  const isClassification = model.task === "classification";

  const grid = useMemo(() => {
    if (!stats) return [];
    const step = (stats.max - stats.min) / (POINTS - 1);
    return Array.from({ length: POINTS }, (_, i) => stats.min + i * step);
  }, [stats]);

  useEffect(() => {
    if (grid.length === 0) return;
    const controller = new AbortController();
    const instances = grid.map((x) => ({ ...debouncedValues, [feature]: x }));

    api
      .predictBatch(instances, controller.signal)
      .then(({ predictions }) => {
        setError(null);
        if (isClassification) {
          const classes = model.classes ?? [];
          setSeries(
            classes.map((c, index) => ({
              name: c,
              colorIndex: index, // cor presa à classe, não à ordem do gráfico
              points: grid.map((x, i): [number, number] => [x, predictions[i].probabilities?.[c] ?? 0]),
            })),
          );
        } else {
          setSeries([
            {
              name: displayName(model, model.target),
              points: grid.map((x, i): [number, number] => [x, Number(predictions[i].prediction)]),
            },
          ]);
        }
      })
      .catch((e: Error) => {
        if (e.name !== "AbortError") setError(e.message);
      });

    return () => controller.abort();
  }, [grid, debouncedValues, feature, isClassification, model]);

  if (!stats) {
    return <p className="muted">Sensibilidade disponível apenas para features numéricas.</p>;
  }
  if (error) return <p className="error">{error}</p>;

  return (
    <LineChart
      label={`Previsão do modelo variando ${displayName(model, feature)}`}
      series={series}
      xName={displayName(model, feature)}
      yFormat={isClassification ? formatPercent : formatDecimal}
      yMin={isClassification ? 0 : undefined}
      yMax={isClassification ? 1 : undefined}
      markerX={Number(values[feature])}
    />
  );
}

import type { ModelInfo, Prediction } from "../api/types";
import { BarChart } from "../charts";
import { displayName, formatDecimal, formatPercent } from "../utils/format";

interface PredictionPanelProps {
  model: ModelInfo;
  prediction: Prediction | null;
  loading: boolean;
}

export function PredictionPanel({ model, prediction, loading }: PredictionPanelProps) {
  if (!prediction) {
    return <p className="muted">{loading ? "Calculando…" : "Ajuste as entradas para ver a previsão."}</p>;
  }

  const classes = model.classes ?? [];
  const probabilities = prediction.probabilities;
  const label = String(prediction.prediction);

  return (
    <div className={`prediction ${loading ? "is-loading" : ""}`} aria-live="polite">
      <div className="hero">
        <span className="hero-label">{displayName(model, model.target)}</span>
        <span className="hero-value">
          {typeof prediction.prediction === "number" ? formatDecimal(prediction.prediction) : label}
        </span>
        {probabilities && <span className="hero-hint">confiança {formatPercent(probabilities[label] ?? 0)}</span>}
      </div>

      {probabilities && classes.length > 0 && (
        <BarChart
          label="Probabilidade por classe"
          categories={classes}
          values={classes.map((c) => probabilities[c] ?? 0)}
          format={formatPercent}
          highlight={label}
          max={1}
          categoryColumn="Classe"
          valueColumn="Probabilidade"
        />
      )}
    </div>
  );
}

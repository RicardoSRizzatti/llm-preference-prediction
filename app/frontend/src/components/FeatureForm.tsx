// Formulário gerado a partir do metadata: funciona para qualquer modelo sem mudar o front.
import type { FeatureValue, FeatureValues, ModelInfo, NumericStats } from "../api/types";
import { displayName } from "../utils/format";

interface FeatureFormProps {
  model: ModelInfo;
  values: FeatureValues;
  onChange: (feature: string, value: FeatureValue) => void;
  onReset: () => void;
}

export function numericStep(stats: NumericStats): number {
  const raw = (stats.max - stats.min) / 100;
  if (raw <= 0) return 0.01;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  return Math.round(raw / magnitude) * magnitude;
}

export function FeatureForm({ model, values, onChange, onReset }: FeatureFormProps) {
  return (
    <form className="feature-form" onSubmit={(e) => e.preventDefault()}>
      {model.features.map((feature) => {
        const stats = model.feature_stats[feature];
        const id = `feature-${feature}`;
        const label = displayName(model, feature);

        if (stats?.type === "categorical") {
          return (
            <div className="field" key={feature}>
              <label htmlFor={id}>{label}</label>
              <select id={id} value={String(values[feature] ?? "")} onChange={(e) => onChange(feature, e.target.value)}>
                {stats.categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          );
        }

        const numeric = stats?.type === "numeric" ? stats : undefined;
        const value = Number(values[feature] ?? 0);
        return (
          <div className="field" key={feature}>
            <div className="field-row">
              <label htmlFor={id}>{label}</label>
              <input
                className="number-input"
                type="number"
                aria-label={`${label} (valor)`}
                value={value}
                step={numeric ? numericStep(numeric) : "any"}
                onChange={(e) => onChange(feature, e.target.valueAsNumber || 0)}
              />
            </div>
            {numeric && (
              <>
                <input
                  id={id}
                  type="range"
                  min={numeric.min}
                  max={numeric.max}
                  step={numericStep(numeric)}
                  value={value}
                  onChange={(e) => onChange(feature, e.target.valueAsNumber)}
                />
                <div className="range-hint">
                  <span>{numeric.min.toLocaleString("pt-BR")}</span>
                  <span>média {numeric.mean.toLocaleString("pt-BR", { maximumFractionDigits: 2 })}</span>
                  <span>{numeric.max.toLocaleString("pt-BR")}</span>
                </div>
              </>
            )}
          </div>
        );
      })}
      <button type="button" className="button-secondary" onClick={onReset}>
        Voltar para a média
      </button>
    </form>
  );
}

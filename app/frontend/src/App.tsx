import { useCallback, useEffect, useState } from "react";

import { api } from "./api/client";
import type { FeatureValue, FeatureValues, ModelInfo, Prediction } from "./api/types";
import { Card } from "./components/Card";
import { FeatureForm } from "./components/FeatureForm";
import { ModelQuality } from "./components/ModelQuality";
import { PredictionPanel } from "./components/PredictionPanel";
import { SensitivityPanel } from "./components/SensitivityPanel";
import { displayName, formatDate } from "./utils/format";
import { useDebounced } from "./utils/useDebounced";

/** Valores iniciais: média das numéricas e primeira categoria das categóricas. */
function defaultValues(model: ModelInfo): FeatureValues {
  return Object.fromEntries(
    model.features.map((f) => {
      const stats = model.feature_stats[f];
      if (stats?.type === "numeric") return [f, Math.round(stats.mean * 100) / 100];
      if (stats?.type === "categorical") return [f, stats.categories[0] ?? ""];
      return [f, 0];
    }),
  );
}

export default function App() {
  const [model, setModel] = useState<ModelInfo | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [values, setValues] = useState<FeatureValues>({});
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [predictError, setPredictError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sensitivityFeature, setSensitivityFeature] = useState<string>("");
  const debouncedValues = useDebounced(values, 120);

  useEffect(() => {
    api
      .model()
      .then((m) => {
        setModel(m);
        setValues(defaultValues(m));
        const firstNumeric = m.features.find((f) => m.feature_stats[f]?.type === "numeric");
        setSensitivityFeature(firstNumeric ?? m.features[0]);
      })
      .catch((e: Error) => setLoadError(e.message));
  }, []);

  // Previsão ao vivo: dispara quando as entradas param de mudar.
  useEffect(() => {
    if (!model || Object.keys(debouncedValues).length === 0) return;
    const controller = new AbortController();
    setLoading(true);
    api
      .predict(debouncedValues, controller.signal)
      .then((p) => {
        setPrediction(p);
        setPredictError(null);
      })
      .catch((e: Error) => {
        if (e.name !== "AbortError") setPredictError(e.message);
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [model, debouncedValues]);

  const updateValue = useCallback((feature: string, value: FeatureValue) => {
    setValues((prev) => ({ ...prev, [feature]: value }));
  }, []);

  if (loadError) {
    return (
      <main className="page">
        <div className="empty-state">
          <h1>Modelo indisponível</h1>
          <p className="error">{loadError}</p>
          <p className="muted">
            Gere o modelo com <code>make all</code> e reinicie a API com <code>make app</code>.
          </p>
        </div>
      </main>
    );
  }

  if (!model) {
    return (
      <main className="page">
        <p className="muted">Carregando modelo…</p>
      </main>
    );
  }

  const numericFeatures = model.features.filter((f) => model.feature_stats[f]?.type === "numeric");
  const commit = model.git?.commit ? `${model.git.commit}${model.git.dirty ? " (alterado)" : ""}` : "—";

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">{model.project ?? "Projeto"}</p>
          <h1>
            {model.title ??
              `${model.task === "classification" ? "Classificação" : "Regressão"}: ${displayName(model, model.target)}`}
          </h1>
        </div>
        <dl className="model-facts">
          <div>
            <dt>Modelo</dt>
            <dd>{model.estimator ?? "—"}</dd>
          </div>
          <div>
            <dt>Treinado em</dt>
            <dd>{formatDate(model.trained_at)}</dd>
          </div>
          <div>
            <dt>Commit</dt>
            <dd>
              <code>{commit}</code>
            </dd>
          </div>
          <div>
            <dt>Amostras</dt>
            <dd>
              {model.n_train ?? "—"} treino · {model.n_test ?? "—"} teste
            </dd>
          </div>
        </dl>
      </header>

      <div className="layout">
        <Card title="Entradas" subtitle="Faixas observadas no treino" className="area-inputs">
          <FeatureForm model={model} values={values} onChange={updateValue} onReset={() => setValues(defaultValues(model))} />
        </Card>

        <Card title="Previsão" subtitle="Atualiza enquanto você ajusta as entradas" className="area-prediction">
          {predictError ? (
            <p className="error">{predictError}</p>
          ) : (
            <PredictionPanel model={model} prediction={prediction} loading={loading} />
          )}
        </Card>

        {numericFeatures.length > 0 && (
          <Card
            title="Sensibilidade"
            subtitle="Como a previsão muda variando uma entrada, com as demais fixas"
            className="area-sensitivity"
            actions={
              <select
                aria-label="Feature analisada"
                value={sensitivityFeature}
                onChange={(e) => setSensitivityFeature(e.target.value)}
              >
                {numericFeatures.map((f) => (
                  <option key={f} value={f}>
                    {displayName(model, f)}
                  </option>
                ))}
              </select>
            }
          >
            <SensitivityPanel model={model} values={values} feature={sensitivityFeature} />
          </Card>
        )}

        <Card title="Qualidade do modelo" subtitle="Métricas do ONNX no conjunto de teste" className="area-quality">
          <ModelQuality model={model} />
        </Card>
      </div>
    </main>
  );
}

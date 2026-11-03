import type { ClassificationMetrics, ModelInfo, RegressionMetrics } from "../api/types";
import { HeatmapChart } from "../charts";
import { formatDecimal, formatPercent } from "../utils/format";
import { StatTile } from "./StatTile";

const confusionTooltip = (real: string, predicted: string, n: number) =>
  `Real: <b>${real}</b><br/>Previsto: <b>${predicted}</b><br/>${n} amostra${n === 1 ? "" : "s"}`;

export function ModelQuality({ model }: { model: ModelInfo }) {
  const metrics = model.metrics;
  if (!metrics) {
    return <p className="muted">Sem métricas. Rode <code>make evaluate</code> para avaliar o modelo.</p>;
  }

  const testHint = model.n_test ? `teste, n = ${model.n_test}` : undefined;

  if (model.task === "regression") {
    const m = metrics as RegressionMetrics;
    return (
      <div className="stat-grid">
        <StatTile label="MAE" value={formatDecimal(m.mae)} hint={testHint} />
        <StatTile label="RMSE" value={formatDecimal(m.rmse)} hint={testHint} />
        <StatTile label="R²" value={formatDecimal(m.r2)} hint={testHint} />
      </div>
    );
  }

  const m = metrics as ClassificationMetrics;
  return (
    <div className="quality">
      <div className="stat-grid stat-grid-2">
        <StatTile label="Acurácia" value={formatPercent(m.accuracy)} hint={testHint} />
        <StatTile label="F1 (macro)" value={formatPercent(m.f1_macro)} hint={testHint} />
        <StatTile label="Precisão (macro)" value={formatPercent(m.precision_macro)} hint={testHint} />
        <StatTile label="Recall (macro)" value={formatPercent(m.recall_macro)} hint={testHint} />
      </div>
      <div className="confusion">
        <h3>Matriz de confusão</h3>
        <HeatmapChart
          label="Matriz de confusão no conjunto de teste"
          xLabels={m.confusion_matrix.labels}
          yLabels={m.confusion_matrix.labels}
          matrix={m.confusion_matrix.matrix}
          xName="Previsto"
          yName="Real"
          tooltip={confusionTooltip}
        />
      </div>
    </div>
  );
}

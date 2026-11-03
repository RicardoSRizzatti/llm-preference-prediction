// Espelha app/api/schemas.py e o models/metadata.json.

export type FeatureValue = number | string;

export interface NumericStats {
  type: "numeric";
  min: number;
  max: number;
  mean: number;
  std: number;
}

export interface CategoricalStats {
  type: "categorical";
  categories: string[];
}

export type FeatureStats = NumericStats | CategoricalStats;

export interface ClassificationMetrics {
  accuracy: number;
  f1_macro: number;
  precision_macro: number;
  recall_macro: number;
  confusion_matrix: { labels: string[]; matrix: number[][] };
  per_class: Record<string, { precision: number; recall: number; "f1-score": number; support: number }>;
}

export interface RegressionMetrics {
  mae: number;
  rmse: number;
  r2: number;
}

export interface ModelInfo {
  project?: string | null;
  title?: string | null;
  task: "classification" | "regression";
  estimator?: string | null;
  trained_at?: string | null;
  evaluated_at?: string | null;
  git?: { commit?: string | null; dirty?: boolean | null } | null;
  features: string[];
  feature_stats: Record<string, FeatureStats>;
  target: string;
  classes?: string[] | null;
  display_names?: Record<string, string>;
  n_train?: number | null;
  n_test?: number | null;
  metrics?: ClassificationMetrics | RegressionMetrics | null;
}

export interface Prediction {
  prediction: FeatureValue;
  probabilities?: Record<string, number> | null;
}

export type FeatureValues = Record<string, FeatureValue>;

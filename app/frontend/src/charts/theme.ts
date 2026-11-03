/**
 * Tema único dos gráficos. TODA cor de gráfico sai daqui — componentes não usam hex solto.
 *
 * Regras (mantenha ao trocar a paleta pela da sua marca):
 * - Categórica em ordem fixa (slot 1, 2, 3...), nunca ciclada; a cor segue a entidade
 *   (ex.: a classe), não a posição no ranking.
 * - Sequencial = um único matiz, claro → escuro (magnitude).
 * - Texto nunca usa a cor da série: valores e rótulos usam as cores de texto.
 * - Modo escuro tem seus próprios tons, não uma inversão automática.
 * A paleta categórica passou no validador de daltonismo (adjacentes; 3 primeiros slots em todos os pares).
 */
import { useEffect, useState } from "react";

export type ColorScheme = "light" | "dark";

export interface ChartTokens {
  surface: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  grid: string;
  axis: string;
  /** Categórica: slots em ordem fixa. */
  series: string[];
  /** Sequencial: do valor mais baixo (perto da superfície) ao mais alto. */
  sequential: string[];
  /** Cor do texto dentro de cada passo da sequencial (branco ou quase preto). */
  sequentialLabel: string[];
  /** Célula vazia (valor zero) em mapas de calor: neutra, recua para a superfície. */
  emptyCell: string;
  emptyCellLabel: string;
  /** Tom de baixa ênfase para marcas secundárias. */
  deemphasis: string;
  tooltipBg: string;
  tooltipBorder: string;
}

export const FONT_FAMILY = 'system-ui, -apple-system, "Segoe UI", sans-serif';

export const tokens: Record<ColorScheme, ChartTokens> = {
  light: {
    surface: "#fcfcfb",
    textPrimary: "#0b0b0b",
    textSecondary: "#52514e",
    textMuted: "#898781",
    grid: "#e1e0d9",
    axis: "#c3c2b7",
    series: ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
    sequential: ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"],
    sequentialLabel: ["#0b0b0b", "#0b0b0b", "#0b0b0b", "#ffffff", "#ffffff", "#ffffff", "#ffffff"],
    emptyCell: "#f0efec",
    emptyCellLabel: "#52514e",
    deemphasis: "#b7d3f6",
    tooltipBg: "#ffffff",
    tooltipBorder: "rgba(11,11,11,0.10)",
  },
  dark: {
    surface: "#1a1a19",
    textPrimary: "#f0efec",
    textSecondary: "#c3c2b7",
    textMuted: "#898781",
    grid: "#2c2c2a",
    axis: "#383835",
    series: ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
    sequential: ["#104281", "#184f95", "#1c5cab", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4"],
    sequentialLabel: ["#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff", "#0b0b0b", "#0b0b0b"],
    emptyCell: "#262625",
    emptyCellLabel: "#c3c2b7",
    deemphasis: "#184f95",
    tooltipBg: "#242423",
    tooltipBorder: "rgba(255,255,255,0.10)",
  },
};

function currentScheme(): ColorScheme {
  const forced = document.documentElement.dataset.theme;
  if (forced === "light" || forced === "dark") return forced;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

/** Esquema de cor atual: segue o sistema, ou <html data-theme="light|dark"> se definido. */
export function useColorScheme(): ColorScheme {
  const [scheme, setScheme] = useState<ColorScheme>(currentScheme);
  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const update = () => setScheme(currentScheme());
    media.addEventListener("change", update);
    const observer = new MutationObserver(update);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => {
      media.removeEventListener("change", update);
      observer.disconnect();
    };
  }, []);
  return scheme;
}

export function useChartTokens(): ChartTokens {
  return tokens[useColorScheme()];
}

/** Cor do slot categórico `index` (ordem fixa; acima de 8 séries, agrupe em "Outros"). */
export function seriesColor(t: ChartTokens, index: number): string {
  return t.series[Math.min(index, t.series.length - 1)];
}

/** Peças comuns a todos os gráficos: fonte, tooltip, animação. */
export function baseOption(t: ChartTokens) {
  return {
    backgroundColor: "transparent",
    textStyle: { fontFamily: FONT_FAMILY, color: t.textSecondary, fontSize: 12 },
    animationDuration: 300,
    animationDurationUpdate: 200,
    tooltip: {
      backgroundColor: t.tooltipBg,
      borderColor: t.tooltipBorder,
      borderWidth: 1,
      padding: [8, 10],
      textStyle: { color: t.textPrimary, fontFamily: FONT_FAMILY, fontSize: 12 },
      extraCssText: "border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,0.12);",
    },
  };
}

/** Eixo de valores: grade em linha fina sólida e recessiva. */
export function valueAxis(t: ChartTokens, extra: Record<string, unknown> = {}) {
  return {
    type: "value" as const,
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: t.textMuted, fontSize: 11 },
    splitLine: { lineStyle: { color: t.grid, width: 1, type: "solid" as const } },
    nameTextStyle: { color: t.textMuted, fontSize: 11 },
    ...extra,
  };
}

/** Eixo de categorias: linha de base discreta, sem grade. */
export function categoryAxis(t: ChartTokens, data: string[], extra: Record<string, unknown> = {}) {
  return {
    type: "category" as const,
    data,
    axisLine: { lineStyle: { color: t.axis } },
    axisTick: { show: false },
    axisLabel: { color: t.textSecondary, fontSize: 12 },
    splitLine: { show: false },
    nameTextStyle: { color: t.textMuted, fontSize: 11 },
    ...extra,
  };
}

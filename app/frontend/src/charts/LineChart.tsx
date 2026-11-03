/**
 * Linhas sobre eixo numérico ou temporal (curvas, séries temporais, sinais).
 * Preparado para escala: amostragem LTTB e zoom (dataZoom) para séries longas.
 * Linhas de 2px, legenda para 2+ séries, rótulo no fim da linha (oculto se colidir),
 * tooltip com crosshair. Use `colorIndex` para manter a cor presa à entidade.
 */
import { useMemo } from "react";

import { Chart } from "./Chart";
import type { ChartOption } from "./echarts";
import { baseOption, seriesColor, useChartTokens, valueAxis } from "./theme";

export interface LineSeries {
  name: string;
  points: [number, number][];
  /** Slot categórico fixo da entidade (padrão: posição na lista). */
  colorIndex?: number;
}

interface LineChartProps {
  label: string;
  series: LineSeries[];
  xName: string;
  yName?: string;
  xType?: "value" | "time";
  xFormat?: (value: number) => string;
  yFormat?: (value: number) => string;
  yMin?: number;
  yMax?: number;
  /** Linha vertical de referência (ex.: valor atual da entrada). */
  markerX?: number;
  /** Ativa zoom/pan; ligado automaticamente acima de 2.000 pontos. */
  zoom?: boolean;
  height?: number;
}

const LARGE_SERIES = 2000;
const defaultXFormat = (v: number) => v.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
const defaultYFormat = (v: number) => v.toLocaleString("pt-BR", { maximumFractionDigits: 3 });

export function LineChart({
  label,
  series,
  xName,
  yName,
  xType = "value",
  xFormat = defaultXFormat,
  yFormat = defaultYFormat,
  yMin,
  yMax,
  markerX,
  zoom,
  height = 300,
}: LineChartProps) {
  const t = useChartTokens();
  const multi = series.length > 1;
  const longest = Math.max(0, ...series.map((s) => s.points.length));
  const useZoom = zoom ?? longest > LARGE_SERIES;

  const option = useMemo<ChartOption>(() => {
    const base = baseOption(t);
    return {
      ...base,
      grid: { left: 8, right: multi ? 96 : 24, top: multi ? 40 : 16, bottom: useZoom ? 72 : 36, containLabel: true },
      legend: multi
        ? {
            top: 0,
            left: 0,
            icon: "roundRect",
            itemWidth: 12,
            itemHeight: 4,
            textStyle: { color: t.textSecondary, fontSize: 12 },
          }
        : undefined,
      tooltip: {
        ...base.tooltip,
        trigger: "axis",
        axisPointer: { type: "line", lineStyle: { color: t.axis, width: 1 } },
        valueFormatter: (v: number) => yFormat(v),
      },
      xAxis: valueAxis(t, {
        type: xType,
        name: xName,
        nameLocation: "middle",
        nameGap: 28,
        min: "dataMin",
        max: "dataMax",
        splitLine: { show: false },
        axisLine: { show: true, lineStyle: { color: t.axis } },
        axisLabel: { color: t.textMuted, fontSize: 11, formatter: xType === "value" ? xFormat : undefined },
      }),
      yAxis: valueAxis(t, {
        name: yName,
        min: yMin,
        max: yMax,
        axisLabel: { color: t.textMuted, fontSize: 11, formatter: yFormat },
      }),
      dataZoom: useZoom
        ? [
            { type: "inside", filterMode: "none" },
            { type: "slider", height: 20, bottom: 8, borderColor: t.grid, textStyle: { color: t.textMuted } },
          ]
        : undefined,
      series: series.map((s, i) => {
        const color = seriesColor(t, s.colorIndex ?? i);
        return {
          name: s.name,
          type: "line",
          data: s.points,
          showSymbol: false,
          symbolSize: 8,
          sampling: "lttb",
          large: s.points.length > LARGE_SERIES,
          color,
          lineStyle: { width: 2, cap: "round", join: "round" },
          emphasis: { focus: "series" },
          endLabel: multi
            ? { show: true, color: t.textSecondary, fontSize: 12, formatter: "{a}", distance: 6 }
            : undefined,
          labelLayout: { hideOverlap: true },
          markLine:
            markerX !== undefined && i === 0
              ? {
                  silent: true,
                  symbol: "none",
                  label: { show: false },
                  lineStyle: { color: t.textMuted, width: 1, type: "solid" },
                  data: [{ xAxis: markerX }],
                }
              : undefined,
        };
      }),
    };
  }, [t, series, multi, useZoom, xName, yName, xType, xFormat, yFormat, yMin, yMax, markerX]);

  const table = useMemo(() => {
    const xs = series[0]?.points.map((p) => p[0]) ?? [];
    return {
      columns: [xName, ...series.map((s) => s.name)],
      rows: xs.map((x, i) => [xFormat(x), ...series.map((s) => yFormat(s.points[i]?.[1] ?? NaN))]),
    };
  }, [series, xName, xFormat, yFormat]);

  return <Chart label={label} option={option} height={height} table={longest <= 500 ? table : undefined} />;
}

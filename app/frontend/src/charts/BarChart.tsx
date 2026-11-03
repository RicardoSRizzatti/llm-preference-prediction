/**
 * Barras horizontais de uma série (ex.: probabilidade por classe).
 * Barra com até 24px, ponta arredondada e base reta; valor na ponta da barra.
 * `highlight` destaca uma categoria; as demais ficam em tom de baixa ênfase.
 */
import { useMemo } from "react";

import { Chart } from "./Chart";
import type { ChartOption } from "./echarts";
import { baseOption, categoryAxis, seriesColor, useChartTokens, valueAxis } from "./theme";

const defaultFormat = (v: number) => v.toLocaleString("pt-BR");

interface BarChartProps {
  label: string;
  categories: string[];
  values: number[];
  format?: (value: number) => string;
  highlight?: string;
  max?: number;
  valueColumn?: string;
  categoryColumn?: string;
}

export function BarChart({
  label,
  categories,
  values,
  format = defaultFormat,
  highlight,
  max,
  valueColumn = "Valor",
  categoryColumn = "Categoria",
}: BarChartProps) {
  const t = useChartTokens();

  const option = useMemo<ChartOption>(() => {
    const accent = seriesColor(t, 0);
    return {
      ...baseOption(t),
      grid: { left: 8, right: 64, top: 8, bottom: 8, containLabel: true },
      xAxis: valueAxis(t, { max, axisLabel: { show: false }, splitLine: { show: false } }),
      yAxis: categoryAxis(t, categories, { inverse: true }),
      tooltip: {
        ...baseOption(t).tooltip,
        trigger: "item",
        formatter: (p: { name: string; value: number }) => `${p.name}<br/><b>${format(p.value)}</b>`,
      },
      series: [
        {
          type: "bar",
          barMaxWidth: 24,
          data: values.map((value, i) => ({
            value,
            itemStyle: {
              color: !highlight || categories[i] === highlight ? accent : t.deemphasis,
              borderRadius: [0, 4, 4, 0],
            },
          })),
          label: {
            show: true,
            position: "right",
            color: t.textSecondary,
            fontSize: 12,
            formatter: (p: { value: number }) => format(p.value),
          },
          emphasis: { disabled: true },
        },
      ],
    };
  }, [t, categories, values, format, highlight, max]);

  return (
    <Chart
      label={label}
      option={option}
      height={Math.max(120, categories.length * 44 + 16)}
      table={{
        columns: [categoryColumn, valueColumn],
        rows: categories.map((c, i) => [c, format(values[i])]),
      }}
    />
  );
}

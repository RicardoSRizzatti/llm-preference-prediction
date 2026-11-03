/**
 * Componente base de todos os gráficos: cria/destrói o ECharts, acompanha o tamanho
 * do container e oferece a visão em tabela (acessibilidade e conferência dos números).
 */
import { useEffect, useRef } from "react";

import { echarts, type ChartInstance, type ChartOption } from "./echarts";

export interface ChartTable {
  columns: string[];
  rows: (string | number)[][];
}

interface ChartProps {
  /** Nome acessível do gráfico (lido por leitores de tela). */
  label: string;
  option: ChartOption;
  height?: number;
  table?: ChartTable;
}

export function Chart({ label, option, height = 280, table }: ChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<ChartInstance | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const chart = echarts.init(el, undefined, { renderer: "canvas" });
    instanceRef.current = chart;
    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(el);
    return () => {
      observer.disconnect();
      chart.dispose();
      instanceRef.current = null;
    };
  }, []);

  useEffect(() => {
    instanceRef.current?.setOption(option, { notMerge: true });
  }, [option]);

  return (
    <figure className="chart">
      <div ref={containerRef} className="chart-canvas" style={{ height }} role="img" aria-label={label} />
      {table && (
        <details className="chart-table">
          <summary>Ver dados em tabela</summary>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  {table.columns.map((c) => (
                    <th key={c}>{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.rows.map((row, i) => (
                  <tr key={i}>
                    {row.map((cell, j) => (
                      <td key={j}>{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </figure>
  );
}

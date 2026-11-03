/**
 * Registro único do ECharts (import modular: só entra no bundle o que está listado aqui).
 * Precisa de outro tipo de gráfico? Registre aqui e crie o componente em charts/.
 */
import { BarChart, HeatmapChart, LineChart } from "echarts/charts";
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  TooltipComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { LabelLayout } from "echarts/features";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([
  BarChart,
  HeatmapChart,
  LineChart,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  TooltipComponent,
  LabelLayout,
  CanvasRenderer,
]);

export { echarts };
export type ChartInstance = ReturnType<typeof echarts.init>;
export type ChartOption = Parameters<ChartInstance["setOption"]>[0];

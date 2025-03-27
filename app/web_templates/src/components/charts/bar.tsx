import useChart from '@/lib/hooks/chart.ts';
import ToolBox from '@/components/charts/toolbox.tsx';
import type { ReactElement, FC } from 'react';
import type { ChartProps } from '@/components/charts/props.ts';
import type { XAXisComponentOption, YAXisComponentOption, TooltipComponentOption } from "echarts/types/dist/echarts";
import type { SeriesOption } from "echarts";
import type { Dimensions } from '@/lib/hooks/chart.ts';

export type HistogramBin = {
    binStart: number;
    binEnd: number;
    count: number;
    label: string;
};

export default function BarChart({ data, labels, tooltipFormatter }: ChartProps): ReactElement<FC> {
    const dimensions: Dimensions = {width: 800, height: 600};
    const xAxis: XAXisComponentOption = {
        type: 'category',
        name: labels != null && labels.x.length > 0 ? labels.x : undefined,
        nameTextStyle: {
            fontSize: 10,
            fontFamily: 'var(--default-font-family, ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji")'
        },
        axisTick: { show: false },
        splitLine: { show: false },
    };
    const yAxis: YAXisComponentOption = {
        type: 'value',
        name: labels != null && labels.y.length > 0 ? labels.y : undefined,
        nameTextStyle: {
            fontSize: 10,
            fontFamily: 'var(--default-font-family, ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji")'
        },
        axisTick: { show: false },
        axisLine: { show: false },
        axisLabel: { show: false },
        splitLine: {lineStyle: { color: '#ccc' }}
    };
    const series: Array<SeriesOption> = [
        {
            type: 'bar',
            datasetIndex: 0,
            barWidth: '100%',
            itemStyle: {
                borderRadius: 2
            },
            encode: {
                x: 'label',
                y: 'count'
            }
        }
    ];
    const tooltipOptions: TooltipComponentOption = {
        formatter: tooltipFormatter,
        trigger: 'axis',
        axisPointer: {
            type: 'shadow',
        }
    };

    const { containerRef, chart } = useChart(data, xAxis, yAxis, series, tooltipOptions);

    return (
        <div className="grid" style={dimensions}>
            <ToolBox features={['save-as', 'zoom', 'restore']} chart={chart} />
            <div ref={containerRef} style={dimensions} />
        </div>
    );
}

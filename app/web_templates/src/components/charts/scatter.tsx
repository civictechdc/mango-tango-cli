import useChart from '@/lib/hooks/chart.ts';
import ToolBox from '@/components/charts/toolbox.tsx';
import type { ReactElement, FC } from 'react';
import type { Dimensions } from '@/lib/hooks/chart.ts';
import type { SeriesOption } from 'echarts';
import type { TopLevelFormatterParams, DatasetOption } from 'echarts/types/dist/shared';
import type { XAXisComponentOption, YAXisComponentOption } from 'echarts/types/dist/echarts'

interface ScatterPlotProps {
    data: DatasetOption | Array<DatasetOption>;
    tooltipFormatter?: (params: TopLevelFormatterParams) => string;
    labels?: {
        x: string;
        y: string;
    };
}

export default function ScatterPlot({ data, labels, tooltipFormatter }: ScatterPlotProps): ReactElement<FC> {
    const dimensions: Dimensions = {width: 800, height: 600};
    const xAxis: XAXisComponentOption = {
        type: 'log',
        name: labels != null && labels.x.length > 0 ? labels.x : undefined,
        nameTextStyle: {
            fontSize: 10,
            fontFamily: 'var(--default-font-family, ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji")'
        },
        axisTick: { show: false },
        splitLine: { show: false },
    };
    const yAxis: YAXisComponentOption = {
        type: 'log',
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
            type: 'scatter',
            encode: {
                x: 'x',
                y: 'y'
            },
            large: true
        }
    ];
    const { containerRef, chart } = useChart(data, xAxis, yAxis, series, tooltipFormatter);

    return (
        <div className="grid" style={dimensions}>
            <ToolBox features={['save-as', 'zoom', 'restore']} chart={chart} />
            <div ref={containerRef} style={dimensions} />
        </div>
    );
}

export type { ScatterPlotProps };
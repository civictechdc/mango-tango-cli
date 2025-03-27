import useChart from '@/lib/hooks/chart.ts';
import ToolBox from '@/components/charts/toolbox.tsx';
import type { ReactElement, FC } from 'react';
import type { SeriesOption } from 'echarts';
import type { XAXisComponentOption, YAXisComponentOption } from 'echarts/types/dist/echarts';
import type { Dimensions } from '@/lib/hooks/chart.ts';
import type { ChartProps } from '@/components/charts/props.ts'

export default function ScatterPlot({ data, labels, tooltipFormatter, axis, seriesEncoding }: ChartProps): ReactElement<FC> {
    const dimensions: Dimensions = {width: 800, height: 600};
    let xAxis: XAXisComponentOption = {
        type: 'log',
        name: labels != null && labels.x.length > 0 ? labels.x : undefined,
        nameTextStyle: {
            fontSize: 10,
            fontFamily: 'var(--default-font-family, ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji")'
        },
        axisTick: { show: false },
        splitLine: { show: false },
    };
    let yAxis: YAXisComponentOption = {
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
    let series: SeriesOption = {
        type: 'scatter',
        encode: {
            x: 'x',
            y: 'y'
        },
        large: true,
        progressive: 0
    };

    if(axis && axis.x) xAxis = {...xAxis, ...axis.x};
    if(axis && axis.y) yAxis = {...yAxis, ...axis.y};
    if(seriesEncoding) series.encode = {...series.encode, ...seriesEncoding};

    const { containerRef, chart } = useChart(data, xAxis, yAxis, series, {formatter: tooltipFormatter});

    return (
        <div className="grid" style={dimensions}>
            <ToolBox features={['save-as', 'zoom', 'restore']} chart={chart} />
            <div ref={containerRef} style={dimensions} />
        </div>
    );
}
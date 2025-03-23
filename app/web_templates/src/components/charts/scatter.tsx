import useChart from '@/lib/hooks/chart.ts';
import type { ReactElement, FC } from 'react';
import type { Dimensions } from '@/lib/hooks/chart.ts';
import type { TopLevelFormatterParams, DatasetOption, XAXisOption, YAxisOption, SeriesOption$1 } from 'echarts';

interface ScatterPlotProps {
    data: DatasetOption | Array<DatasetOption>;
    labels: {
        x: string;
        y: string;
    };
    tooltipFormatter: (params: TopLevelFormatterParams) => string;
}

export default function ScatterPlot({ data, labels, tooltipFormatter }: ScatterPlotProps): ReactElement<FC> {
    const dimensions: Dimensions = {width: 800, height: 600};
    const xAxis: XAXisOption = {
        type: 'log',
        name: labels != null && labels.x.length > 0 ? labels.x : 'X',
    };
    const yAxis: YAxisOption = {
        type: 'log',
        name: labels != null && labels.y.length > 0 ? labels.y : 'Y',
    };
    const series: SeriesOption$1 = [
        {
            type: 'scatter',
            encode: {
                x: 'x',
                y: 'y'
            }
        }
    ];
    const { containerRef } = useChart(data, xAxis, yAxis, series, tooltipFormatter);

    return <div id="scatter-chart" ref={containerRef} style={dimensions} />;
}

export type { ScatterPlotProps };
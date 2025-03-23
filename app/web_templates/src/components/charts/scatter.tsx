import useChart from '@/lib/hooks/chart.ts';
import type { ReactElement, FC } from 'react';
import type { Dimensions } from '@/lib/hooks/chart.ts';
import type { TopLevelFormatterParams, DatasetOption } from 'echarts/types/dist/shared';
import type { SeriesOption } from 'echarts';
import type {XAXisComponentOption, YAXisComponentOption} from 'echarts/types/dist/echarts'

interface ScatterPlotProps {
    data: DatasetOption | Array<DatasetOption>;
    labels: {
        x: string;
        y: string;
    };
    tooltipFormatter?: (params: TopLevelFormatterParams) => string;
}

export default function ScatterPlot({ data, labels, tooltipFormatter }: ScatterPlotProps): ReactElement<FC> {
    const dimensions: Dimensions = {width: 800, height: 600};
    const xAxis: XAXisComponentOption = {
        type: 'log',
        name: labels != null && labels.x.length > 0 ? labels.x : 'X',
    };
    const yAxis: YAXisComponentOption = {
        type: 'log',
        name: labels != null && labels.y.length > 0 ? labels.y : 'Y',
    };
    const series: Array<SeriesOption> = [
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
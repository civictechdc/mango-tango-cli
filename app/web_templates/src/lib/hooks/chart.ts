import { useRef, useEffect } from 'react';
import { init } from 'echarts';
import type { RefObject } from 'react';
import type { EChartsOption, EChartsType, SeriesOption } from 'echarts';
import type { TopLevelFormatterParams, DatasetOption } from 'echarts/types/dist/shared';
import type { XAXisComponentOption, YAXisComponentOption } from 'echarts/types/dist/echarts';

export type DataPoint = {
    x: number;
    y: number;
    [index: string]: any;
};

export type ChartProperties = {
    containerRef: RefObject<any>;
};

export type Dimensions = {
    width: number;
    height: number;
};

export type DataPoints = Array<DataPoint>;

export default function useChart(
    data: DatasetOption | Array<DatasetOption>,
    xAxis: XAXisComponentOption | Array<XAXisComponentOption>,
    yAxis: YAXisComponentOption | Array<YAXisComponentOption>,
    series: SeriesOption | Array<SeriesOption>,
    tooltipFormatter?: (params: TopLevelFormatterParams) => string,
): ChartProperties {
    const containerRef = useRef<any>(null);
    const chartRef = useRef<EChartsType | null>(null);

    useEffect(() => {
        if (!containerRef.current) return;

        const chartOptions: EChartsOption = {
            tooltip: {
                show: true,
                formatter: tooltipFormatter,
                className: 'items-start min-w-[8rem] gap-1.5 rounded-lg dark:border-zinc-800/50',
                backgroundColor: 'var(--color-white)',
                borderColor: '#e4e4e780',
                borderRadius: undefined,
                textStyle: {
                    fontSize: 12,
                    fontFamily: 'var(--default-font-family, ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji")'
                },
                extraCssText: 'display: grid;--tw-shadow: 0 20px 25px -5px var(--tw-shadow-color, rgb(0 0 0 / 0.1)), 0 8px 10px -6px var(--tw-shadow-color, rgb(0 0 0 / 0.1));box-shadow: var(--tw-inset-shadow), var(--tw-inset-ring-shadow), var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow);'

            },
            dataset: data,
            xAxis: xAxis,
            yAxis: yAxis,
            series: series
        };

        chartRef.current = init(containerRef.current);
        chartRef.current.setOption(chartOptions);

        return () => {
            chartRef.current?.dispose();
        };
    }, []);

    useEffect(() => {
        if(chartRef.current == null) return;

        chartRef.current.setOption({dataset: data}, {replaceMerge: ['dataset'], silent: true});
    }, [data]);

    return {
        containerRef,
    };
}
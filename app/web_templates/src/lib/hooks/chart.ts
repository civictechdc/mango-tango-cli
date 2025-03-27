import { useRef, useEffect, useState } from 'react';
import { init } from 'echarts';
import type { RefObject } from 'react';
import type { EChartsOption, EChartsType, SeriesOption } from 'echarts';
import type { DatasetOption } from 'echarts/types/dist/shared';
import type { XAXisComponentOption, YAXisComponentOption, TooltipComponentOption } from 'echarts/types/dist/echarts';

export type ChartProperties = {
    containerRef: RefObject<any>;
    chart: EChartsType | null;
};

export type Dimensions = {
    width: number;
    height: number;
};

export default function useChart(
    data: DatasetOption | Array<DatasetOption>,
    xAxis: XAXisComponentOption | Array<XAXisComponentOption>,
    yAxis: YAXisComponentOption | Array<YAXisComponentOption>,
    series: SeriesOption | Array<SeriesOption>,
    tooltipOptions: TooltipComponentOption,
): ChartProperties {
    const containerRef = useRef<any>(null);
    const [chart, setChart] = useState<EChartsType | null>(null);

    useEffect(() => {
        if (!containerRef.current) return;

        let chartOptions: EChartsOption = {
            tooltip: {
                show: true,
                className: 'items-start min-w-[8rem] gap-1.5 rounded-lg dark:border-zinc-800/50 dark:bg-zinc-900! dark:text-zinc-100!',
                backgroundColor: 'var(--color-white)',
                borderColor: '#e4e4e780',
                borderRadius: undefined,
                textStyle: {
                    fontSize: 12,
                    fontFamily: 'var(--default-font-family, ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji")'
                },
                extraCssText: 'display: grid;--tw-shadow: 0 20px 25px -5px var(--tw-shadow-color, rgb(0 0 0 / 0.1)), 0 8px 10px -6px var(--tw-shadow-color, rgb(0 0 0 / 0.1));box-shadow: var(--tw-inset-shadow), var(--tw-inset-ring-shadow), var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow);',
                ...tooltipOptions
            },
            toolbox: {
                show: false,
                right: 72,
                itemSize: 16,
                feature: {
                    saveAsImage: {},
                    restore: {},
                    dataZoom: {}
                }
            },
            brush: {
                xAxisIndex: 0,
                yAxisIndex: 0,
                throttleType: 'debounce',
                throttleDelay: 100
            },
            dataZoom: [
                {type: 'inside', realtime: false}
            ],
            dataset: data,
            xAxis: xAxis,
            yAxis: yAxis,
            series: series,
        };

        const chartInstance: EChartsType = init(containerRef.current) as EChartsType;

        chartInstance.setOption(chartOptions);
        setChart(chartInstance);

        return () => {
            chartInstance.dispose();
            setChart(null);
        };
    }, []);

    useEffect(() => {
        chart?.setOption({dataset: data}, {replaceMerge: ['dataset'], silent: true});
    }, [data]);


    return {
        containerRef,
        chart
    };
}
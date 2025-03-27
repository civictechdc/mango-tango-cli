import { useMemo } from 'react';
import BarChart from '@/components/charts/bar.tsx';
import type { ReactElement, FC } from 'react';
import type { DatasetOption, TopLevelFormatterParams } from 'echarts/types/dist/shared';
import type { ChartContainerProps } from '@/components/charts/props.ts';

export type HistogramBin = {
    binStart: number;
    binEnd: number;
    count: number;
    label: string;
};

export default function HistogramChart({ presenter }: ChartContainerProps): ReactElement<FC> {
    const data = useMemo<Array<DatasetOption>>(() => {
        if (presenter == null) return [];

        const rawData = presenter.x as Array<number>;
        const binCount = 50;
        const minValue = Math.min(...rawData);
        const maxValue = Math.max(...rawData);
        const binWidth = (maxValue - minValue) / binCount;
        const bins: Array<HistogramBin> = Array.from({length: binCount}, (_, index: number): HistogramBin => {
            const binStart = minValue + index * binWidth;
            const binEnd = binStart + binWidth;

            return {
                binStart: binStart,
                binEnd: binEnd,
                count: 0,
                label: `${Math.floor(binStart)} - ${Math.floor(binEnd)}`,
            };
        });

        for (const value of rawData) {
            const binIndex = Math.min(Math.floor((value - minValue) / binWidth), binCount - 1);

            if (binIndex >= 0 && binIndex < bins.length) bins[binIndex].count++;
        }

        return [{
            dimensions: ['binStart', 'binEnd', 'count', 'label'],
            source: bins.filter((bin: HistogramBin): boolean => bin.count > 0)
        }];
    }, [presenter]);
    const tooltipFormatter = (params: TopLevelFormatterParams): string => {
        const param: TopLevelFormatterParams = Array.isArray(params) ? params[0] : params;

        if(!param.data) return '';

        const data = param.data as HistogramBin;

        return `
            <div class="grid gap-1.5">
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    <span class="font-bold">Message Count</span>
                    <span>${data.count}</span>
                </div>
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    <span class="font-bold">${data.label}</span>
                </div>
            </div>
        `;
    };

    return <BarChart data={data} tooltipFormatter={tooltipFormatter} seriesEncoding={{x: 'label', y: 'count'}} />;
}
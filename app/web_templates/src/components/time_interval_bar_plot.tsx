import { useMemo } from 'react';
import BarChart from '@/components/charts/bar.tsx';
import type { ReactElement, FC } from 'react';
import type {DatasetOption, TopLevelFormatterParams} from 'echarts/types/dist/shared';
import type { ChartContainerProps } from '@/components/charts/props.ts';

export type TimeIntervalBarPlotDataPoint = {
    x: string;
    y: number;
};

export default function TimeIntervalChart({ presenter }: ChartContainerProps): ReactElement<FC> {
    const data = useMemo<Array<DatasetOption>>(() => {
        const rawX = presenter.x as Array<string>;
        const rawY = presenter.y as Array<number>;

        return [{
            dimensions: ['x', 'y'],
            source: Array.from({length: rawX.length}, (_, index: number): TimeIntervalBarPlotDataPoint => ({
                x: rawX[index],
                y: rawY[index]
            }))
        }];
    }, [presenter]);
    const tooltipFormatter = (params: TopLevelFormatterParams): string => {
        const param: TopLevelFormatterParams = Array.isArray(params) ? params[0] : params;

        if(!param.data) return '';

        const data = param.data as TimeIntervalBarPlotDataPoint;

        return `
            <div class="grid gap-1.5">
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    <span class="font-bold">${presenter.axis.x.label}</span>
                    <span>${data.x}</span>
                </div>
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    <span class="font-bold">${presenter.axis.y.label}</span>
                    <span>${data.y}</span>
                </div>
            </div>
        `;
    };

    return <BarChart data={data} tooltipFormatter={tooltipFormatter} />;
}
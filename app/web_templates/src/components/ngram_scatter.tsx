import { useMemo } from 'react';
import ScatterPlot from '@/components/charts/scatter.tsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.tsx';
import type { ReactElement, FC } from 'react';
import type { ChartContainerProps } from '@/components/charts/props.ts';
import type { PresenterAxisData } from '@/lib/data/presenters.ts';
import type {TopLevelFormatterParams, DatasetOption} from 'echarts/types/dist/shared';

export type NgramScatterPlotDataPoint = {
    ngram: string;
    x: number;
    y: number;
};

export default function NgramScatterPlot({ presenter }: ChartContainerProps): ReactElement<FC> {
    const totalRepetitionData= useMemo<DatasetOption>((): DatasetOption => {
        let dataset: DatasetOption = {dimensions: ['ngram', 'x', 'y']};

        if (presenter == null) return dataset;

        const rawNgrams = presenter.ngrams as Array<string>;
        const rawX = presenter.x as Array<number>;
        const rawY = (presenter.y as PresenterAxisData)['total_repetition'] as Array<number>;

        dataset.source = Array.from({length: rawX.length}, (_, index: number): NgramScatterPlotDataPoint => ({
            ngram: rawNgrams[index],
            x: rawX[index],
            y: rawY[index],
        }));

        return dataset;
    }, [presenter]);
    const amplificationFactorData= useMemo<DatasetOption>((): DatasetOption => {
        let dataset: DatasetOption = {dimensions: ['ngram', 'x', 'y']};

        if (presenter == null) return dataset;

        const rawNgrams = presenter.ngrams as Array<string>;
        const rawX = presenter.x as Array<number>;
        const rawY = (presenter.y as PresenterAxisData)['amplification_factor'] as Array<number>;

        dataset.source = Array.from({length: rawX.length}, (_, index: number): NgramScatterPlotDataPoint => ({
            ngram: rawNgrams[index],
            x: rawX[index],
            y: rawY[index],
        }));

        return dataset;
    }, [presenter]);
    const totalRepetitionTooltipFormatter = (params: TopLevelFormatterParams): string => {
        const param: TopLevelFormatterParams = Array.isArray(params) ? params[0] : params;

        if(!param.data) return '';

        const data = param.data as NgramScatterPlotDataPoint;

        return `
            <div class="grid gap-1.5">
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    <span class="font-bold">${data.ngram}</span>
                </div>
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    <span class="font-bold">Total Repetition:</span>
                    <span>${data.x}</span>
                </div>
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    <span class="font-bold">User Repetition:</span>
                    <span>${data.y}</span>
                </div>
            </div>
        `;
    };
    const amplificationFactorTooltipFormatter = (params: TopLevelFormatterParams): string => {
        const param: TopLevelFormatterParams = Array.isArray(params) ? params[0] : params;

        if(!param.data) return '';

        const data = param.data as NgramScatterPlotDataPoint;

        return `
            <div class="grid gap-1.5">
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    <span class="font-bold">${data.ngram}</span>
                </div>
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    <span class="font-bold">Total Repetition:</span>
                    <span>${data.x}</span>
                </div>
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    
                    <span class="font-bold">Amplification Factor:</span>
                    <span>${data.y}</span>
                </div>
            </div>
        `;
    };

    return (
        <Tabs defaultValue="total_repetition" className="items-center">
            <TabsList>
                <TabsTrigger value="total_repetition">Total Repetition</TabsTrigger>
                <TabsTrigger value="amplification_factor">Amplification Factor</TabsTrigger>
            </TabsList>
            <TabsContent value="total_repetition">
                <ScatterPlot data={totalRepetitionData} tooltipFormatter={totalRepetitionTooltipFormatter} />
            </TabsContent>
            <TabsContent value="amplification_factor">
                <ScatterPlot data={amplificationFactorData} tooltipFormatter={amplificationFactorTooltipFormatter} />
            </TabsContent>
        </Tabs>
    );
}
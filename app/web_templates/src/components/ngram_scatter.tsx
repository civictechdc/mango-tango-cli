import { useMemo, useState, Suspense } from 'react';
import { useTheme } from '@/components/theme-provider.tsx';
import ScatterPlot from '@/components/charts/scatter.tsx';
import SearchBar from '@/components/search.tsx';
import DataTable from '@/components/data_table.tsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.tsx';
import { TooltipProvider, Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip.tsx';
import { Info } from 'lucide-react';
import type { ReactElement, FC } from 'react';
import type { GridColumn } from '@glideapps/glide-data-grid';
import type { DataPoint } from '@/lib/types/datapoint';
import type { ChartContainerProps } from '@/components/charts/props.ts';
import type { PresenterAxisData } from '@/lib/data/presenters.ts';

export type NgramScatterPlotDataPoint = DataPoint & {
    ngram: string;
    ranking: number;
};

export type NgramScatterPlotYAxisType = 'total_repetition' | 'amplification_factor';

export default function NgramScatterPlot({ presenter }: ChartContainerProps): ReactElement<FC> {
    const [searchValue, setSearchValue] = useState<string>('');
    const [currentTab, setCurrentTab] = useState<NgramScatterPlotYAxisType>('total_repetition');
    const {theme} = useTheme();
    const isDark = useMemo<boolean>(() =>
            (theme === 'system' &&  window.matchMedia("(prefers-color-scheme: dark)").matches) || theme === 'dark'
    , [theme]);
    const dataTableColumns = useMemo<Array<GridColumn>>(() => ([
        { id: 'ranking', title: 'Ranking', width: 100 },
        { id: 'ngram', title: 'Ngram', width: 400 },
        { id: 'x', title: 'User Repetition', width: 150 },
        {
            id: 'y',
            width: 150,
            title: currentTab === 'total_repetition' ? 'Total Repetition' : 'Amplification Factor'
        },
    ]), [currentTab]);
    const data = useMemo<Array<NgramScatterPlotDataPoint>>(() => {
        if (presenter == null) return [];

        const dataSourceLength: number = (presenter.ngrams as Array<string>).length;
        let dataSource = new Array<NgramScatterPlotDataPoint>();
        let dataSourceIndex: number = 0;


        for(let index: number = 0; index < dataSourceLength; index++) {



            if(searchValue.length > 0) {
                if(!((presenter.ngrams as Array<string>)[index].includes(searchValue))) continue;


                dataSource[dataSourceIndex] = {
                    ngram: (presenter.ngrams as Array<string>)[index],
                    x: (presenter.x as Array<number>)[index],
                    y: ((presenter.y as PresenterAxisData)[currentTab] as Array<number>)[index],
                    ranking: dataSourceIndex + 1
                };
                dataSourceIndex++;
                continue;
            }

            dataSource[index] = {
                ngram: (presenter.ngrams as Array<string>)[index],
                x: (presenter.x as Array<number>)[index],
                y: ((presenter.y as PresenterAxisData)[currentTab] as Array<number>)[index],
                ranking: index + 1
            };

        }

        return dataSource;
    }, [presenter, searchValue, currentTab]);

    const handleSearchSubmit = (value: string) => setSearchValue(value);
    const handleSearchClear = () => setSearchValue('');
    const handleTabChange = (value: string) => setCurrentTab(value as NgramScatterPlotYAxisType);

    const totalRepetitionTooltipFormatter = (params: NgramScatterPlotDataPoint): string => {
        return `
            <div class="grid gap-1.5">
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    <span class="font-bold">${params.ngram}</span>
                </div>
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                                 <span class="font-bold">Ranking:</span>
                                 <span>${params.ranking}</span>
                </div>
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    <span class="font-bold">Total Repetition:</span>
                    <span>${params.x}</span>
                </div>
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    <span class="font-bold">User Repetition:</span>
                    <span>${params.y}</span>
                </div>
            </div>
        `;
    };
    const amplificationFactorTooltipFormatter = (params: NgramScatterPlotDataPoint): string => {
        return `
            <div class="grid gap-1.5">
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    <span class="font-bold">${params.ngram}</span>
                </div>
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                                 <span class="font-bold">Ranking:</span>
                                 <span>${params.ranking}</span>
                </div>
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    <span class="font-bold">Total Repetition:</span>
                    <span>${params.x}</span>
                </div>
                <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                    
                    <span class="font-bold">Amplification Factor:</span>
                    <span>${params.y}</span>
                </div>
            </div>
        `;
    };
    const SearchComponent: ReactElement<FC> | null = presenter.ngrams ? (
        <SearchBar
            searchList={presenter.ngrams}
            onSubmit={handleSearchSubmit}
            onClear={handleSearchClear}
            placeholder="Search Ngram Here..." />
    ): null;
    let ScatterPlotComponent: ReactElement<FC> | null = null;

    if(currentTab === 'total_repetition') ScatterPlotComponent = (
        <Suspense fallback={<p>Loading...</p>}>
            <ScatterPlot data={data} darkMode={isDark} tooltip={totalRepetitionTooltipFormatter} />
        </Suspense>
    );
    if(currentTab === 'amplification_factor') ScatterPlotComponent = (
        <Suspense fallback={<p>Loading...</p>}>
            <ScatterPlot data={data} darkMode={isDark} tooltip={amplificationFactorTooltipFormatter} />
        </Suspense>
    );

    return (
        <TooltipProvider>
            <Tabs value={currentTab} onValueChange={handleTabChange} className="items-center">
                <TabsList>
                    <TabsTrigger value="total_repetition">Total Repetition</TabsTrigger>
                    <TabsTrigger value="amplification_factor">Amplification Factor</TabsTrigger>
                </TabsList>
                <TabsContent value="total_repetition">
                    <div className="grid grid-flow-col row-span-1 justify-end">
                        <Tooltip delayDuration={300}>
                            <TooltipTrigger>
                                <Info className="size-6" />
                            </TooltipTrigger>
                            <TooltipContent>
                                {presenter.explanation['total_repetition']}
                            </TooltipContent>
                        </Tooltip>
                    </div>
                    <div className="grid grid-flow-col row-span-1 my-4">{SearchComponent}</div>
                    {ScatterPlotComponent}
                    <div className="grid grid-flow-col row-span-1 my-4">
                        <DataTable darkMode={isDark} columns={dataTableColumns} data={data} />
                    </div>
                </TabsContent>
                <TabsContent value="amplification_factor">
                    <div className="grid grid-flow-col row-span-1 justify-end">
                        <Tooltip delayDuration={300}>
                            <TooltipTrigger><Info /></TooltipTrigger>
                            <TooltipContent>
                                {presenter.explanation['amplification_factor']}
                            </TooltipContent>
                        </Tooltip>
                    </div>
                    <div className="grid grid-flow-col row-span-1 my-4">{SearchComponent}</div>
                    {ScatterPlotComponent}
                    <div className="grid grid-flow-col row-span-1 my-4">
                        <DataTable darkMode={isDark} columns={dataTableColumns} data={data} />
                    </div>
                </TabsContent>
            </Tabs>
        </TooltipProvider>
    );
}
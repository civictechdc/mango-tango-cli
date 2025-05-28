import { useMemo, useState, useEffect, useRef } from 'react';
import { useTheme } from '@/components/theme-provider.tsx';
import { fetchPresenter } from '@/lib/data/presenters.ts';
import { CompactSelection } from '@glideapps/glide-data-grid';
import ScatterPlot from '@/components/charts/scatter.tsx';
import SearchBar from '@/components/search.tsx';
import DataTable from '@/components/data_table.tsx';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.tsx';
import { TooltipProvider, Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip.tsx';
import { Info } from 'lucide-react';
import type { ReactElement, FC } from 'react';
import type { PickingInfo } from '@deck.gl/core';
import type { GridColumn, GridSelection, DataEditorRef } from '@glideapps/glide-data-grid';
import type { DataPoint } from '@/lib/types/datapoint';
import type { Presenter, PresenterAxisData } from '@/lib/types/presenters';
import type { ColumnsAlignmentProperties } from '@/components/data_table';
import type { ChartContainerProps } from '@/components/charts/props.ts';

export type NgramScatterPlotDataPointStats = DataPoint & {
    ngram: string;
};

export type NgramScatterPlotDataPointFull = NgramScatterPlotDataPointStats & {
    user: string;
    userReps: number;
    upn: number;
    message: string;
    timestamp: string;
};

export type NgramPresenterStats = Presenter & {
    ngrams: Array<string>;
};

export type NgramPresenterFull = NgramPresenterStats & {
    users: Array<string>;
    user_reps: Array<number>;
    upns: Array<number>;
    messages: Array<string>;
    timestamps: Array<string>;
};

export type NgramScatterPlotDataPoint = NgramScatterPlotDataPointStats | NgramScatterPlotDataPointFull;
export type NgramScatterPlotYAxisType = 'total_repetition' | 'amplification_factor';

export default function NgramScatterPlot({ presenter }: ChartContainerProps<NgramPresenterStats>): ReactElement<FC> {
    const dataTableRef = useRef<DataEditorRef | null>(null);
    const dataTableRef2 = useRef<DataEditorRef | null>(null);
    const [searchValue, setSearchValue] = useState<string>('');
    const [selectedNgram, setSelectedNgram] = useState<string>('');
    const [rowGridSelection, setRowGridSelection] = useState<CompactSelection>(CompactSelection.empty());
    const [selectedPresenter, setSelectedPresenter] = useState<NgramPresenterFull | null>(null);
    const [currentTab, setCurrentTab] = useState<NgramScatterPlotYAxisType>('total_repetition');
    const { theme } = useTheme();
    const isDark = useMemo<boolean>(() =>
            (theme === 'system' &&  window.matchMedia("(prefers-color-scheme: dark)").matches) || theme === 'dark'
    , [theme]);
    const dataTableColumns = useMemo<Array<GridColumn>>(() => {
        if(selectedNgram) return [
            { id: 'ngram', title: 'Ngram', width: 200 },
            { id: 'user', title: 'User', width: 150 },
            { id: 'userReps', title: 'User Reps', width: 75 },
            { id: 'upn', title: 'UPN', width: 75 },
            { id: 'message', title: 'Post Content', width: 500 },
            { id: 'timestamp', title: 'Timestamp', width: 225 },
        ];

        return [
            { id: 'ngram', title: 'Ngram', width: 400 },
            { id: 'x', title: 'User Repetition', width: 150 },
            {
                id: 'y',
                width: 150,
                title: currentTab === 'total_repetition' ? 'Total Repetition' : 'Amplification Factor'
            },
        ];
    }, [currentTab, selectedNgram]);
    const data = useMemo<Array<NgramScatterPlotDataPoint>>(() => {
        const currentPresenter: NgramPresenterStats | NgramPresenterFull = selectedPresenter ?? presenter;
        const dataSourceLength: number = (currentPresenter.ngrams as Array<string>).length;
        const rawNgrams = currentPresenter.ngrams as Array<string>;
        const rawX = currentPresenter.x as Array<number>;
        const rawY = currentPresenter.y as PresenterAxisData;
        let dataSource = new Array<NgramScatterPlotDataPoint>();
        let dataSourceIndex: number = 0;

        for(let index: number = 0; index < dataSourceLength; index++) {
            if(searchValue.length > 0) {
                if(!(rawNgrams[index].includes(searchValue))) continue;
                if(!selectedPresenter) dataSource[dataSourceIndex] = {
                    ngram: rawNgrams[index],
                    x: rawX[index],
                    y: (rawY[currentTab] as Array<number>)[index]
                };
                if(selectedPresenter) {
                    const rawCurrentPresenter = currentPresenter as NgramPresenterFull;
                    dataSource[dataSourceIndex] = {
                        ngram: rawNgrams[index],
                        x: rawX[index],
                        y: (rawY[currentTab] as Array<number>)[index],
                        user: rawCurrentPresenter.users[index],
                        userReps: rawCurrentPresenter.user_reps[index],
                        upn: rawCurrentPresenter.upns[index],
                        message: rawCurrentPresenter.messages[index],
                        timestamp: rawCurrentPresenter.timestamps[index]
                    };
                }

                dataSourceIndex++;
                continue;
            }

            if(!selectedPresenter) dataSource[index] = {
                ngram: rawNgrams[index],
                x: rawX[index],
                y: (rawY[currentTab] as Array<number>)[index]
            };
            if(selectedPresenter) {
                const rawCurrentPresenter = currentPresenter as NgramPresenterFull;
                dataSource[index] = {
                    ngram: rawNgrams[index],
                    x: rawX[index],
                    y: (rawY[currentTab] as Array<number>)[index],
                    user: rawCurrentPresenter.users[index],
                    userReps: rawCurrentPresenter.user_reps[index],
                    upn: rawCurrentPresenter.upns[index],
                    message: rawCurrentPresenter.messages[index],
                    timestamp: rawCurrentPresenter.timestamps[index]
                };
            }

        }

        return dataSource;
    }, [selectedPresenter, searchValue, currentTab]);
    const onNgramSelect = (item: NgramScatterPlotDataPointStats | null, selectionChange?: GridSelection): void => {
        setSelectedNgram(item ? item.ngram : '');
        if(selectionChange) setRowGridSelection(selectionChange.rows);
    };
    const onDeckClick = (item: PickingInfo<NgramScatterPlotDataPointStats>): void => setSelectedNgram(item.object ? item.object.ngram : '');
    const handleSearchSubmit = (value: string) => setSearchValue(value);
    const handleSearchClear = () => setSearchValue('');
    const handleTabChange = (value: string) => setCurrentTab(value as NgramScatterPlotYAxisType);
    const totalRepetitionTooltipFormatter = (params: NgramScatterPlotDataPoint): string => `
        <div class="grid gap-1.5">
            <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                <span class="font-bold">${params.ngram}</span>
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
    const amplificationFactorTooltipFormatter = (params: NgramScatterPlotDataPoint): string => `
        <div class="grid gap-1.5">
            <div class="[&>svg]:text-zinc-500 flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 dark:[&>svg]:text-zinc-400">
                <span class="font-bold">${params.ngram}</span>
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
    const columnAlignment: ColumnsAlignmentProperties = {
        x: 'center',
        y: 'center',
    };

    useEffect(() => {
        if(selectedNgram.length === 0 && !selectedPresenter) return;
        if(selectedNgram.length === 0 && selectedPresenter) {
            setSelectedPresenter(null);
            return;
        }

        const controller = new AbortController();

        (async (): Promise<void> => {
            const fullPresenter = await fetchPresenter<NgramPresenterFull>(presenter.id, controller.signal, {
                output: 'full',
                filter_field: 'ngram',
                filter_value: selectedNgram
            });

            if(fullPresenter) {
                let ngramIndex: number = 0;
                const ngramLength: number = fullPresenter.ngrams.length;

                for(let index: number = 0; index < ngramLength; index++) {
                    if(selectedNgram === fullPresenter.ngrams[index]) {
                        ngramIndex = index;
                        break;
                    }
                }

                setSelectedPresenter(fullPresenter);
                setRowGridSelection((state: CompactSelection): CompactSelection => {
                    const firstRowSelection: number | undefined = state.first();

                    if(firstRowSelection) return state.remove(firstRowSelection).add(ngramIndex);

                    return state.add(ngramIndex);
                });
                if(dataTableRef.current && currentTab === 'total_repetition') dataTableRef.current.scrollTo(
                    0,
                    ngramIndex,
                    'vertical',
                    0,
                    0,
                    {vAlign: 'center'}
                );
                if(dataTableRef2.current && currentTab === 'amplification_factor') dataTableRef2.current.scrollTo(
                    0,
                    ngramIndex,
                    'vertical',
                    0,
                    0,
                    {vAlign: 'center'}
                );
            }
        })();

        return () => controller.abort();
    }, [selectedNgram]);

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
                    <div className="grid grid-flow-col row-span-1 my-4">
                        <SearchBar
                            searchList={presenter.ngrams as Array<string>}
                            onSubmit={handleSearchSubmit}
                            onClear={handleSearchClear}
                            placeholder="Search Ngram Here..." />
                    </div>
                    <ScatterPlot
                        data={data}
                        darkMode={isDark}
                        onClick={onDeckClick}
                        tooltip={totalRepetitionTooltipFormatter} />
                    <div className="grid grid-flow-col row-span-1 my-4">
                        <DataTable
                            ref={dataTableRef}
                            darkMode={isDark}
                            columns={dataTableColumns}
                            columnContentAlignment={columnAlignment}
                            rowSelection={rowGridSelection}
                            onSelect={onNgramSelect}
                            data={data} />
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
                    <div className="grid grid-flow-col row-span-1 my-4">
                        <SearchBar
                            searchList={presenter.ngrams as Array<string>}
                            onSubmit={handleSearchSubmit}
                            onClear={handleSearchClear}
                            placeholder="Search Ngram Here..." />
                    </div>
                    <ScatterPlot
                        data={data}
                        darkMode={isDark}
                        onClick={onDeckClick}
                        tooltip={amplificationFactorTooltipFormatter} />
                    <div className="grid grid-flow-col row-span-1 my-4">
                        <DataTable
                            ref={dataTableRef2}
                            darkMode={isDark}
                            columns={dataTableColumns}
                            columnContentAlignment={columnAlignment}
                            rowSelection={rowGridSelection}
                            onSelect={onNgramSelect}
                            data={data} />
                    </div>
                </TabsContent>
            </Tabs>
        </TooltipProvider>
    );
}
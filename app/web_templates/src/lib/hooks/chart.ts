import { useState, useMemo, useCallback } from 'react';
import { OrthographicView } from '@deck.gl/core';
import { scaleLog, scaleLinear, scaleOrdinal } from '@visx/scale';
import { calculatePosition } from '@/lib/axis';
import type { OrthographicViewState, ViewStateChangeParameters, PickingInfo, Deck } from '@deck.gl/core';
import type { DeckGLProps } from '@deck.gl/react';
import type { AnyD3Scale } from '@visx/scale';
import type { ChartAxisSettingsType, AxisScaleType, AxisType } from '@/lib/types/axis';
import type { TooltipContent, TooltipFunction } from '@/lib/types/tooltip';
import type { Dimensions, DimensionMargins } from '@/lib/types/dimensions';
import type { ChartDataPoint, ChartDataPoints, DataPoint } from '@/lib/types/datapoint';
import type { ChartViewStateHooks } from '@/lib/types/zoom';

export type CustomDeckGLProps = DeckGLProps<OrthographicView>;

export type ChartProperties<DataPointType> = {
    data: ChartDataPoints<DataPointType>;
    deckProps: CustomDeckGLProps;
    viewport: {
        viewState: OrthographicViewState;
        hooks: ChartViewStateHooks;
        visibleData: Array<PickingInfo<ChartDataPoint<DataPointType> & DataPoint>>;
    };
    axis: {
        x: AxisScaleType;
        y: AxisScaleType;
    };
};

export type BaseScale = {
    xDomain: [number, number] | Set<string>;
    yDomain: [number, number] | Set<string>;
    xAxis: AxisType;
    yAxis: AxisType;
} | null;

const MIN_LOG_VALUE: number = 0.9;

export default function useChart<DataPointType>(
    data: Array<DataPoint & DataPointType>,
    tooltip: TooltipFunction<DataPointType>,
    deck: Deck<OrthographicView> | null,
    axis?: ChartAxisSettingsType,
    dimensions?: Dimensions
): ChartProperties<DataPointType> {
    const width: number = dimensions?.width ?? 800;
    const height: number = dimensions?.height ?? 600;
    const margin: DimensionMargins = dimensions?.margins ?? { top: 60, right: 60, bottom: 80, left: 80 };
    const initViewState: OrthographicViewState = {
        target: [width / 2, height / 2, 0],
        zoom: 0
    };
    const [viewState, setViewState] = useState<OrthographicViewState>(initViewState);
    const [baseScales, setBaseScale] = useState<BaseScale>(null);
    const { plotData, xScale, yScale } = useMemo(() => {
        const dataLength: number = data.length;

        if (!data || dataLength === 0) {
            return { plotData: [], xScale: null, yScale: null };
        }

        const xAxisType: AxisType = axis?.x?.type ?? 'linear';
        const yAxisType: AxisType = axis?.y?.type ?? 'linear';
        let maxXValue: number = 0;
        let maxYValue: number = 0;
        let minXValue: number = Infinity;
        let minYValue: number = Infinity;
        const xCategoryValues = new Set<string>();
        const yCategoryValues = new Set<string>();
        let plotData: ChartDataPoints<DataPointType & DataPoint> = new Array(dataLength);

        for(let index = 0; index < dataLength; index++) {
            const point = data[index] as (DataPoint & DataPointType);
            if(xAxisType === 'category') xCategoryValues.add(data[index].x as string);
            if(yAxisType === 'category') yCategoryValues.add(data[index].y as string);
            if(xAxisType !== 'category') {
                const x = point.x as number;

                if(x > maxXValue) maxXValue = x;
                if(x < minXValue) minXValue = x;
            }
            if(yAxisType !== 'category') {
                const y = point.y as number;

                if(y > maxYValue) maxYValue = y;
                if(y < minYValue) minYValue = y;
            }
        }

        console.log(`x: min=${minXValue}, max=${maxXValue}`);
        console.log(`y: min=${minYValue}, max=${maxYValue}`);

        if(xAxisType !== 'category' && minXValue === Infinity) {
            minXValue = xAxisType === 'log' ? MIN_LOG_VALUE : 0;

        } else if(xAxisType === 'log' && minXValue <= 0) {
            minXValue = MIN_LOG_VALUE;
        }

        if(yAxisType !== 'category' && minYValue === Infinity) {
            minYValue = yAxisType === 'log' ? MIN_LOG_VALUE : 0;

        } else if(yAxisType === 'log' && minYValue <= 0) {
            minYValue = MIN_LOG_VALUE;
        }

        let xDomain: [number, number] | Set<string> = xAxisType === 'category' ? xCategoryValues : [minXValue * 0.9, maxXValue * 1.1];
        let yDomain: [number, number] | Set<string> = yAxisType === 'category' ? yCategoryValues : [minYValue * 0.9, maxYValue * 1.1];
        let xScale: AnyD3Scale | null = null;
        let yScale: AnyD3Scale | null = null;

        if(xAxisType === 'linear') xScale = scaleLinear({
            domain: xDomain as [number, number],
            range: [margin.left, width - margin.right],
            clamp: true
        });

        if(xAxisType === 'log') xScale = scaleLog({
            domain: xDomain as [number, number],
            range: [margin.left, width - margin.right],
            clamp: true
        });

        if(xAxisType === 'category') {
            const xCatCount: number = (xDomain as Set<string>).size;
            const xStep: number = (width - margin.left - margin.right) / (xCatCount <= 1 ? 1 : xCatCount - 1);
            const xRange: Array<number> = Array.from({length: xCatCount}, (_, index: number): number => margin.left + index * xStep);

            xScale = scaleOrdinal({
                domain: Array.from(xDomain as Set<string>),
                range: xRange,
            });
        }

        if(yAxisType === 'linear') yScale = scaleLinear({
            domain: yDomain as [number, number],
            range: [height - margin.bottom, margin.top],
            clamp: true
        });

        if(yAxisType === 'log') yScale = scaleLog({
            domain: yDomain as [number, number],
            range: [height - margin.bottom, margin.top],
            clamp: true
        });

        if(yAxisType === 'category') {
            const yCatCount = (yDomain as Set<string>).size;
            const yStep = (height - margin.top - margin.bottom) / (yCatCount <= 1 ? 1 : yCatCount - 1);
            const yRange = Array.from({ length: yCatCount }, (_, index: number): number => height - margin.bottom - index * yStep);

            yScale = scaleOrdinal({
                domain: Array.from(yDomain as Set<string>),
                range: yRange
            });
        }

        if(!baseScales) setBaseScale({
            xDomain,
            yDomain,
            xAxis: xAxisType,
            yAxis: yAxisType,
        });

        for(let index = 0; index < dataLength; index++) {
            plotData[index] = {
                ...data[index],
                position: [0, 0],
                color: [99, 130, 191]
            };

            if(xScale) plotData[index].position[0] = calculatePosition(xScale, data[index].x);
            if(yScale) plotData[index].position[1] = calculatePosition(yScale, data[index].y);
        }


        return { plotData, xScale, yScale };
    }, [data, width, height, margin, baseScales]);
    const visibleData = useMemo(() => {
        console.log('deck instance: ', deck);
        if(!deck) return [];

        const viewport = deck.getViewports()[0];

        if(!viewport) return [];

        console.log('Zoom level:', viewState.zoom);
        console.log('Viewport width:', viewport.width, 'height:', viewport.height, 'zoom: ', viewport.zoom);
        console.log('viewport: ', viewport);

        return deck.pickObjects({
            x: 0,
            y: 0,
            width: viewport.width,
            height: viewport.height,

        });
    }, [deck, viewState.target, viewState.zoom]);
    const updatedScales = useMemo(() => {
        console.log('Recalculating scales with zoom level:', viewState.zoom);
        if (!baseScales || !xScale || !yScale) {
            console.log('scales not initialized. exiting early...');
            return { xScale, yScale };
        }

        if(visibleData.length === 0){
            console.log('no visible points. exiting early...');
            return { xScale, yScale };
        }

        if(viewState.zoom === 0){
            console.log('not zoomed in. exiting early...');
            return { xScale, yScale };
        }

        const { xAxis, yAxis } = baseScales;
        let maxX = -Infinity;
        let maxY = -Infinity;
        let minX = Infinity;
        let minY = Infinity;
        const xCategoryValues = new Set<string>();
        const yCategoryValues = new Set<string>();
        const visibleDataLength: number = visibleData.length;

        console.log('visible data array size:', visibleDataLength);

        for(let index = 0; index < visibleDataLength; index++) {
            const point = visibleData[index].object as (DataPoint & DataPointType);

            if(xAxis === 'category') xCategoryValues.add(point.x as string);
            if(yAxis === 'category') yCategoryValues.add(point.y as string);
            if(xAxis !== 'category') {
                const x = point.x as number;

                if(x > maxX) maxX = x;
                if(x < minX) minX = x;
            }
            if(yAxis !== 'category') {
                const y = point.y as number;

                if(y > maxY) maxY = y;
                if(y < minY) minY = y;
            }
        }

        console.log(`x: min=${minX}, max=${maxX}`);
        console.log(`y: min=${minY}, max=${maxY}`);

        if (xAxis !== 'category' && (minX === Infinity || maxX === -Infinity)) {
            // Fall back to the original domain if no visible data
            const originalDomain = (xScale as any).domain();
            minX = originalDomain[0];
            maxX = originalDomain[1];
            console.log('Using fallback X domain:', [minX, maxX]);
        }

        if (yAxis !== 'category' && (minY === Infinity || maxY === -Infinity)) {
            // Fall back to the original domain if no visible data
            const originalDomain = (yScale as any).domain();
            minY = originalDomain[0];
            maxY = originalDomain[1];
            console.log('Using fallback Y domain:', [minY, maxY]);
        }

        if (xAxis === 'log' && minX <= 0) {
            minX = MIN_LOG_VALUE;
        }

        if (yAxis === 'log' && minY <= 0) {
            minY = MIN_LOG_VALUE;
        }

        if (xAxis !== 'category' && viewState.zoom === 0) {
            minX = Math.max(minX * 0.9, xAxis === 'log' ? MIN_LOG_VALUE : 0);
            maxX *= 1.1;
        }

        if (yAxis !== 'category' && viewState.zoom === 0) {
            minY = Math.max(minY * 0.9, yAxis === 'log' ? MIN_LOG_VALUE : 0);
            maxY *= 1.1;
        }

        // Create new scales based on visible data
        let newXScale = xScale;
        let newYScale = yScale;

        if (xAxis === 'linear') newXScale = scaleLinear({
            domain: [minX * 0.9, maxX * 1.1],
            range: [margin.left, width - margin.right],
            clamp: true
        });

        if (xAxis === 'log') newXScale = scaleLog({
            domain: [minX, maxX],
            range: [margin.left, width - margin.right],
            clamp: true
        });

        if (xAxis === 'category') {
            const xCategories = Array.from(xCategoryValues);
            const xCatCount = xCategories.length;
            const xStep = (width - margin.left - margin.right) / (xCatCount <= 1 ? 1 : xCatCount - 1);
            const xRange = Array.from({length: xCatCount}, (_, i) => margin.left + i * xStep);

            newXScale = scaleOrdinal({
                domain: xCategories,
                range: xRange,
            });
        }

        if (yAxis === 'linear') newYScale = scaleLinear({
            domain: [minY, maxY],
            range: [height - margin.bottom, margin.top],
            clamp: true
        });

        if (yAxis === 'log') newYScale = scaleLog({
            domain: [minY, maxY],
            range: [height - margin.bottom, margin.top],
            clamp: true
        });

        if (yAxis === 'category') {
            const yCategories = Array.from(yCategoryValues);
            const yCatCount = yCategories.length;
            const yStep = (height - margin.top - margin.bottom) / (yCatCount <= 1 ? 1 : yCatCount - 1);
            const yRange = Array.from({length: yCatCount}, (_, i) => height - margin.bottom - i * yStep);

            newYScale = scaleOrdinal({
                domain: yCategories,
                range: yRange,
            });
        }

        return {
            xScale: newXScale,
            yScale: newYScale,
        };
    }, [visibleData, baseScales, width, height, margin, xScale, yScale, viewState.target, viewState.zoom]);
    const onViewStateChange = useCallback(({viewState}: ViewStateChangeParameters) => {
        console.log('ViewState change:', viewState);
        setViewState(viewState);
    }, [deck]);
    const incrementZoom = (step: number = 1): void => {
        setViewState((state: OrthographicViewState): OrthographicViewState => ({...state, zoom: (state.zoom as number) + step}));
        if(deck) deck.setProps({
            views: new OrthographicView({
                id: 'custom-view',
                viewState: {
                    ...viewState,
                    zoom: (viewState.zoom as number) + step
                }
            })
        });
    };
    const decrementZoom = (step: number = 1): void => {
        setViewState((state: OrthographicViewState): OrthographicViewState => {
            const zoom = state.zoom as number;

            if(zoom > 0) return {
                ...state,
                zoom: zoom - step
            };

            return {
                target: initViewState.target,
                zoom: 0
            };
        });

        if(deck) {
            const zoom = viewState.zoom as number;

            deck.setProps({
                views: new OrthographicView({
                    id: 'custom-view',
                    viewState: {
                        ...viewState,
                        zoom: zoom > 0 ? zoom - step : 0
                    }
                })
            });
        }
    };
    const resetViewState = (): void => {
        setViewState(initViewState);

        if(deck) deck.setProps({
            views: new OrthographicView({
                id: 'custom-view',
                viewState: initViewState
            })
        });
    };
    const renderTooltip = ({object, x, y}: PickingInfo<DataPointType>): TooltipContent => {
        if (!object) {
            return null;
        }

        let tooltipStyles = {
            backgroundColor: 'var(--color-white)',
            color: '#000',
            padding: '8px 12px',
            fontSize: '12px'
        };
        const edgeOfChart = width * 0.8;
        const bottomOfChart = height * 0.85;
        const transformValueX: number | undefined = x >= edgeOfChart ? x - (width - edgeOfChart) : undefined;
        const transformValueY: number | undefined = y >= bottomOfChart ? y - (height - bottomOfChart) : undefined;

        if(transformValueX || transformValueY) return {
            html: tooltip(object as DataPointType),
            className: 'border rounded-lg shadow-xl border-zinc-200 items-start min-w-[8rem] gap-1.5 rounded-lg dark:border-zinc-800 dark:bg-zinc-950! dark:text-zinc-100!',
            style: {
                ...tooltipStyles,
                transform: `translate(${transformValueX ?? x}px, ${transformValueY ?? y}px)`
            }
        };

        return {
            html: tooltip(object as DataPointType),
            style: tooltipStyles,
            className: 'border rounded-lg shadow-xl border-zinc-200 items-start min-w-[8rem] gap-1.5 rounded-lg dark:border-zinc-800 dark:bg-zinc-950! dark:text-zinc-100!'
        };
    };

    return {
        data: plotData,
        axis: {
            x: { scale: updatedScales.xScale as AnyD3Scale },
            y: { scale: updatedScales.yScale as AnyD3Scale }
        },
        viewport: {
            viewState: viewState,
            visibleData: visibleData,
            hooks: {
                increment: incrementZoom,
                decrement: decrementZoom,
                reset: resetViewState
            }
        },
        deckProps: {
            views: new OrthographicView({id: 'custom-view'}),
            viewState: viewState,
            onViewStateChange: onViewStateChange,
            controller: {
                doubleClickZoom: false,
                inertia: true,
                touchRotate: false,
                scrollZoom: false,
                dragPan: (viewState.zoom as number) > 0
            },
            width: width - (margin.left + margin.right),
            height: height - (margin.top + margin.bottom),
            style: {
              top: `${margin.top}px`,
              left: `${margin.left}px`
            },
            getTooltip: renderTooltip
        }
    };
}
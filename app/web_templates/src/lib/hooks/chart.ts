import { useState, useMemo, useCallback } from 'react';
import { scaleLog, scaleLinear, scaleOrdinal, ScaleLinear, ScaleLogarithmic } from 'd3-scale';
import { OrthographicView } from '@deck.gl/core';
import { calculatePosition } from '@/lib/axis';
import type { ScaleOrdinal } from 'd3-scale';
import type { OrthographicViewState, ViewStateChangeParameters, MapViewState, PickingInfo, View } from '@deck.gl/core';
import type { DeckGLProps } from '@deck.gl/react';
import type { ChartAxisSettingsType, AxisScaleType, AxisType, DynamicScale, AxisTicks } from '@/lib/types/axis';
import type { TooltipContent, TooltipFunction } from '@/lib/types/tooltip';
import type { Dimensions, DimensionMargins } from '@/lib/types/dimensions';
import type { ChartDataPoints, DataPoint } from '@/lib/types/datapoint';

export type CustomDeckGLProps = Omit<DeckGLProps, 'views'> & {
    views: View;
};

export type ChartProperties<DataPointType> = {
    data: ChartDataPoints<DataPointType>;
    deckProps: CustomDeckGLProps;
    axis: {
        x: AxisScaleType;
        y: AxisScaleType;
    };
};

export default function useChart<DataPointType>(
    data: Array<DataPoint & DataPointType>,
    tooltip: TooltipFunction<DataPointType>,
    axis?: ChartAxisSettingsType,
    dimensions?: Dimensions,
): ChartProperties<DataPointType> {
    const width: number = dimensions?.width ?? 800;
    const height: number = dimensions?.height ?? 600;
    const margin: DimensionMargins = dimensions?.margins ?? { top: 60, right: 60, bottom: 80, left: 80 };
    const [viewState, setViewState] = useState<OrthographicViewState>({
        target: [width / 2, height / 2, 0],
        zoom: 0
    });
    const { plotData, xScale, yScale, xTicks, yTicks } = useMemo(() => {
        const dataLength: number = data.length;

        if (!data || dataLength === 0) {
            return { plotData: [], xScale: null, yScale: null, xTicks: [], yTicks: [] };
        }

        const xAxisType: AxisType = axis?.x?.type ?? 'linear';
        const yAxisType: AxisType = axis?.y?.type ?? 'linear';
        let maxXValue: number = 0;
        let maxYValue: number = 0;
        let minXValue: number = Infinity;
        let minYValue: number = Infinity;
        const xCategoryValues = new Set<string>();
        const yCategoryValues = new Set<string>();
        let plotData: ChartDataPoints<DataPointType> = new Array(dataLength);

        for(let index = 0; index < dataLength; index++) {
            if(xAxisType === 'category') xCategoryValues.add(data[index].x as string);
            if(yAxisType === 'category') yCategoryValues.add(data[index].y as string);
            if(xAxisType !== 'category') {
                if((data[index].x as number) > maxXValue) maxXValue = data[index].x as number;
                if((data[index].x as number) < minXValue) minXValue = data[index].x as number;
            }
            if(yAxisType !== 'category') {
                if((data[index].y as number) > maxYValue) maxYValue = data[index].y as number;
                if((data[index].y as number) < minYValue) minYValue = data[index].y as number;
            }
        }

        if(xAxisType !== 'category' && minXValue === Infinity) minXValue = xAxisType === 'log' ? 1 : 0;
        if(yAxisType !== 'category' && minYValue === Infinity) minYValue = yAxisType === 'log' ? 1 : 0;

        let xDomain = xAxisType === 'category' ? xCategoryValues : [minXValue, maxXValue];
        let yDomain = yAxisType === 'category' ? yCategoryValues : [minYValue, maxYValue];
        let xScale: DynamicScale | null = null;
        let yScale: DynamicScale | null = null;

        if(xAxisType === 'linear') xScale = scaleLinear()
            .domain(xDomain as [number, number])
            .range([margin.left, width - margin.right])
            .clamp(true);

        if(xAxisType === 'log'){
            let domain = xDomain as [number, number];
            const minPower = Math.floor(Math.log10(domain[0]));
            const minDomain = Math.pow(10, minPower);
            const maxPower = Math.ceil(Math.log10(domain[1]));
            const maxDomain = Math.pow(10, maxPower);
            domain[0] = minPower === 0 ? minDomain * 0.9 : minDomain;
            domain[1] = maxDomain * 1.1;
            xDomain = domain;
            xScale = scaleLog()
                .domain(domain)
                .range([margin.left, width - margin.right])
                .clamp(true);
        }

        if(xAxisType === 'category') {
            const xCatCount = (xDomain as Set<string>).size;
            const xStep = (width - margin.left - margin.right) / (xCatCount <= 1 ? 1 : xCatCount - 1);
            const xRange = Array.from({ length: xCatCount }, (_, i) => margin.left + i * xStep);

            xScale = (scaleOrdinal() as ScaleOrdinal<string, number, any>)
                .domain(xDomain as Set<string>)
                .range(xRange);
        }

        if(yAxisType === 'linear') yScale = scaleLinear()
            .domain(yDomain as [number, number])
            .range([height - margin.bottom, margin.top])
            .clamp(true);

        if(yAxisType === 'log') {
            let domain = yDomain as [number, number];
            const minPower = Math.floor(Math.log10(domain[0]));
            const minDomain = Math.pow(10, minPower);
            const maxPower = Math.ceil(Math.log10(domain[1]));
            const maxDomain = Math.pow(10, maxPower);
            domain[0] = minPower === 0 ? minDomain * 0.9 : minDomain;
            domain[1] = maxDomain * 1.1;
            yDomain = domain;
            yScale = scaleLog()
                .domain(domain)
                .range([height - margin.bottom, margin.top])
                .clamp(true);
        }

        if(yAxisType === 'category') {
            const yCatCount = (yDomain as Set<string>).size;
            const yStep = (height - margin.top - margin.bottom) / (yCatCount <= 1 ? 1 : yCatCount - 1);
            const yRange = Array.from({ length: yCatCount }, (_, i) => height - margin.bottom - i * yStep);

            yScale = (scaleOrdinal() as ScaleOrdinal<string, number, any>)
                .domain(yDomain as Set<string>)
                .range(yRange);
        }


        for(let index = 0; index < dataLength; index++) {
            plotData[index] = {
                ...data[index],
                position: [0, 0],
                color: [99, 130, 191]
            };

            if(xScale != null) plotData[index].position[0] = calculatePosition(xScale, data[index].x, xAxisType);
            if(yScale != null) plotData[index].position[1] = calculatePosition(yScale, data[index].y, yAxisType)
        }

        let xTicks: AxisTicks = xAxisType === 'category' ?
            [...new Set(xDomain as Set<string>)] :
            (xScale as (ScaleLinear<number, number> | ScaleLogarithmic<number, number>)).ticks(
                xAxisType === 'log' ? Math.round(Math.log((xDomain as [number, number])[1]) / Math.log(10)) : 3
            );
        let yTicks: AxisTicks = yAxisType === 'category' ?
            [... new Set(yDomain as Set<string>)] :
            (yScale as (ScaleLinear<number, number> | ScaleLogarithmic<number, number>)).ticks(
                yAxisType === 'log' ? Math.round(Math.log((yDomain as [number, number])[1]) / Math.log(10)) : 3
            );


        return { plotData, xScale, yScale, xTicks, yTicks };
    }, [data, width, height, margin]);
    const onViewStateChange = useCallback(({viewState}: ViewStateChangeParameters) => {
        setViewState(viewState);
    }, []);
    const renderTooltip = ({object, x, y}: PickingInfo<DataPointType>): TooltipContent => {
        if (!object) {
            return null;
        }

        let tooltipStyles = {
            zIndex: 10,
            backgroundColor: 'oklch(0.21 0.006 285.885)',
            color: '#fff',
            borderColor: '#e4e4e780',
            padding: '8px 12px',
            borderRadius: '12px',
            fontSize: '12px',
            boxShadow: 'var(--tw-inset-shadow), var(--tw-inset-ring-shadow), var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow)',
            '--tw-shadow': '0 20px 25px -5px var(--tw-shadow-color, rgb(0 0 0 / 0.1)), 0 8px 10px -6px var(--tw-shadow-color, rgb(0 0 0 / 0.1))'
        };
        const edgeOfChart = width * 0.8;
        const bottomOfChart = height * 0.85;
        const transformValueX: number | undefined = x >= edgeOfChart ? x - (width - edgeOfChart) : undefined;
        const transformValueY: number | undefined = y >= bottomOfChart ? y - (height - bottomOfChart) : undefined;

        if(transformValueX || transformValueY) return {
            html: tooltip(object as DataPointType),
            style: {
                ...tooltipStyles,
                transform: `translate(${transformValueX ?? x}px, ${transformValueY ?? y}px)`
            }
        };

        return {
            html: tooltip(object as DataPointType),
            style: tooltipStyles,
        };
    };

    return {
        data: plotData,
        axis: {
            x: {
                scale: xScale as DynamicScale,
                ticks: xTicks
            },
            y: {
                scale: yScale as DynamicScale,
                ticks: yTicks
            }
        },
        deckProps: {
            views: new OrthographicView({
                clear: true
            }),
            viewState: viewState as MapViewState,
            onViewStateChange: onViewStateChange,
            controller: {
                doubleClickZoom: false,
                inertia: true,
                touchRotate: false,
                dragPan: false
            },
            width: width,
            height: height,
            getTooltip: renderTooltip
        }
    };
}
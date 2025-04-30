import useChart from '@/lib/hooks/chart.ts';
import { ScatterplotLayer } from '@deck.gl/layers';
import { COORDINATE_SYSTEM } from '@deck.gl/core';
import DeckGL from '@deck.gl/react';
import ChartAxes from '@/components/charts/axis.tsx';
import type { ReactElement, FC } from 'react';
import type { ChartProps } from '@/components/charts/props.ts';

export default function ScatterPlot({
    data,
    tooltip,
    darkMode = true,
    axis = {x: {type: 'log'}, y: {type: 'log'}},
    dimensions = {width: 800, height: 600, margins: { top: 60, right: 60, bottom: 80, left: 80 }}}: ChartProps): ReactElement<FC> {
    const {data: plotData, deckProps, axis: chartAxes} = useChart(data, tooltip, axis);
    const layers = [
        new ScatterplotLayer({
            id: `scatter-${Math.random().toString(36)}`,
            data: plotData,
            pickable: true,
            opacity: 0.8,
            stroked: false,
            filled: true,
            radiusScale: 6,
            radiusMinPixels: 2.5,
            radiusMaxPixels: 6,
            coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
            getPosition: d => d.position,
            getFillColor: d => d.color,
            updateTriggers: {
                getFillColor: [darkMode]  // Only update colors when darkMode changes
            },
            transitions: {
                getPosition: {
                    type: 'spring',
                    stiffness: 0.5,
                    damping: 0.5,
                    duration: 300
                },
                getFillColor: {
                    duration: 300
                }
            },
            parameters: {
                depthTest: false // Can improve performance for 2D visualization
            }
        })
    ];

    return (
        <div style={{ position: 'relative', width: dimensions.width, height: dimensions.height, zIndex: 0 }}>
            <DeckGL {...deckProps} layers={layers} />
            {axis && (
                <ChartAxes
                    dimensions={dimensions}
                    xAxis={{
                        ...chartAxes.x,
                        type: axis?.x?.type,
                        label: axis?.x?.label,
                        showGridLines: axis?.x?.showGridLines
                    }}
                    yAxis={{
                        ...chartAxes.y,
                        type: axis?.y?.type,
                        label: axis?.y?.label,
                        showGridLines: axis?.y?.showGridLines
                    }}
                    darkMode={darkMode}
                />
            )}
        </div>
    );
}
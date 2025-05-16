import { useMemo, useRef, useState } from 'react';
import useChart from '@/lib/hooks/chart.ts';
import { ScatterplotLayer } from '@deck.gl/layers';
import { COORDINATE_SYSTEM } from '@deck.gl/core';
import DeckGL from '@deck.gl/react';
import { AxisLeft, AxisBottom } from '@visx/axis';
import ToolBox from '@/components/charts/toolbox.tsx';
import type { ReactElement, FC } from 'react';
import type { Deck, OrthographicView } from '@deck.gl/core';
import type { DeckGLRef } from '@deck.gl/react';
import type { ChartProps } from '@/components/charts/props.ts';

export default function ScatterPlot({
    data,
    tooltip,
    darkMode = false,
    axis = {x: {type: 'log', show: true}, y: {type: 'log', show: true}},
    dimensions = {width: 800, height: 600, margins: { top: 20, right: 40, bottom: 21, left: 40 }}
}: ChartProps): ReactElement<FC> {
    const axesFillColor = useMemo<string>(() => darkMode ? '#fff' : '#000', [darkMode]);
    const [deckInstance, setDeckInstance] = useState<Deck<OrthographicView> | null>(null);
    const deckRef = useRef<DeckGLRef<OrthographicView> | null>(null);
    const {data: plotData, deckProps, axis: chartAxes, viewport} = useChart(data, tooltip, deckInstance, axis, dimensions);
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
                getFillColor: [darkMode, viewport.viewState.zoom]
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
                depthTest: false
            }
        })
    ];

    console.log('visible data in view port: ', viewport.visibleData);
    return (
        <>
            <div className="grid grid-flow-col justify-end">
                <div className="grid grid-flow-row">
                    <ToolBox
                        features={['zoom', 'restore']}
                        zoomIncrement={viewport.hooks.increment}
                        zoomDecrement={viewport.hooks.decrement}
                        zoomReset={viewport.hooks.reset} />
                </div>
            </div>
            <div style={{ position: 'relative', width: dimensions.width, height: dimensions.height, zIndex: 0 }}>
                <DeckGL {...deckProps}
                        ref={deckRef}
                        layers={layers}
                        onAfterRender={() => {
                            if(deckRef.current != null && deckInstance == null) setDeckInstance(deckRef.current?.deck as Deck<OrthographicView>);
                        }}/>
                <svg
                    width={dimensions.width}
                    height={dimensions.height}>
                    {(axis.x && axis.x.show) && (
                        <AxisBottom scale={chartAxes.x.scale}
                                top={dimensions.height - (dimensions.margins?.bottom as number)}
                                tickLabelProps={{
                                    fill: axesFillColor,
                                    fontSize: 10,
                                    textAnchor: 'middle'
                                }}
                                stroke={axesFillColor}
                                tickStroke={axesFillColor} />
                    )}
                    {(axis.y && axis.y.show) && (
                        <AxisLeft scale={chartAxes.y.scale}
                              left={dimensions.margins?.left as number}
                              tickLabelProps={{
                                  fill: axesFillColor,
                                  fontSize: 10,
                                  textAnchor: 'end'
                              }}
                              stroke={axesFillColor}
                              tickStroke={axesFillColor} />
                    )}
                </svg>
            </div>
        </>
    );
}
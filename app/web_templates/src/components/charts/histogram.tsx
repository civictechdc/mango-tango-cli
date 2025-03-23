import { useMemo } from 'react';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
import type { ReactElement, FC } from 'react';
import {HistogramBin} from "@/components/example_histogram.tsx";

type HistogramData = Array<number>;

interface HistogramProps {
    data: HistogramData;
}

export default function Histogram({ data }: HistogramProps): ReactElement<FC> {
    const layers = useMemo(() => {
        const binCount = 50;
        const maxValue = Math.max(...data);
        const binWidth = maxValue / binCount;
        const bins: Array<HistogramBin> = Array.from({length: binCount}, (_, index: number): HistogramBin => {
            const binStart = maxValue + index * binWidth;
            const binEnd = binStart + binWidth;

            return {
                binStart: binStart,
                binEnd: binEnd,
                count: 0,
                label: `${Math.floor(binStart)} - ${Math.floor(binEnd)}`,
            };
        });

        for (const value of data) {
            if (value > maxValue) continue;

            const binIndex = Math.min(Math.floor(value / binWidth), binCount - 1);

            if (binIndex >= 0 && binIndex < bins.length) bins[binIndex].count++;
        }

        return [
            new ScatterplotLayer({
                id: 'scatter-layer',
                data: bins,
                pickable: true,
                opacity: 0.8,
                stroked: true,
                filled: true,
                radiusScale: 6,
                radiusMinPixels: 1,
                radiusMaxPixels: 100,
                lineWidthMinPixels: 1
            })
        ];
    }, [data]);

    return (
        <div>
            <DeckGL controller={true} layers={layers} style={{ position: 'relative' }} />
        </div>
    );
}

export type { HistogramProps, HistogramData };
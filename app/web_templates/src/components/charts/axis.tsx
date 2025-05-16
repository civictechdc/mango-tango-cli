import type { ReactElement, FC } from 'react';
import type { AxesProps } from '@/lib/types/axis';

export function ChartAxes({ dimensions }: AxesProps): ReactElement<FC> {
    return (
        <svg width={dimensions.width} height={dimensions.height} style={{
            position: 'absolute',
            top: 0,
            left: 0,
            pointerEvents: 'none',
            fontFamily: 'sans-serif',
            fontSize: '12px',
            zIndex: -1
        }}>

        </svg>
    );
}
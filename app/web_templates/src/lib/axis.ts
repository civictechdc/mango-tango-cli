import type { ScaleLinear, ScaleLogarithmic, ScaleOrdinal } from 'd3-scale';
import type { AxisType, DynamicScale } from '@/lib/types/axis';

export function isLinearScale(scale: DynamicScale): scale is ScaleLinear<number, number> {
    return (scale as any).ticks !== undefined && (scale as any).interpolate !== undefined;
}

export function isLogScale(scale: DynamicScale): scale is ScaleLogarithmic<number, number> {
    return (scale as any).base !== undefined;
}

export function isOrdinalScale(scale: DynamicScale): scale is ScaleOrdinal<string, number, never> {
    return (scale as any).domain !== undefined && (scale as any).unknown !== undefined;
}

export function calculatePosition(scale: DynamicScale, value: string | number, scaleType: AxisType): number {
    try {
        if(scaleType === 'category' && isOrdinalScale(scale)) return scale(value as string);
        if(scaleType === 'log' && isLogScale(scale)) return scale(Math.max((value as number) || 1, 1));
        if(scaleType === 'linear' && isLinearScale(scale)) return scale(value as number);

    } catch(err){
        console.error('Error calculating position:', err);
    }

    return 0;
}

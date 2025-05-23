import type { AnyD3Scale, ScaleConfigToD3Scale, LinearScaleConfig, LogScaleConfig, OrdinalScaleConfig } from '@visx/scale';

export function isLinearScale(scale: AnyD3Scale): boolean {
    return (scale as ScaleConfigToD3Scale<LinearScaleConfig>).ticks !== undefined &&
        (scale as ScaleConfigToD3Scale<LinearScaleConfig>).interpolate !== undefined;
}

export function isLogScale(scale: AnyD3Scale): boolean {
    return (scale as ScaleConfigToD3Scale<LogScaleConfig>).base !== undefined;
}

export function isOrdinalScale(scale: AnyD3Scale): boolean {
    return (scale as ScaleConfigToD3Scale<OrdinalScaleConfig>).domain !== undefined &&
        (scale as ScaleConfigToD3Scale<OrdinalScaleConfig>).unknown !== undefined;
}

export function calculatePosition(scale: AnyD3Scale, value: string | number): number {
    try {
        if(isOrdinalScale(scale)) return (scale as ScaleConfigToD3Scale<OrdinalScaleConfig>)(value as string) as number ?? 0;
        if(isLogScale(scale)) return scale(Math.max((value as number) || 0.9, 0.9));
        if(isLinearScale(scale)) return scale(value as number);

    } catch(err){
        console.error('Error calculating position:', err);
    }

    return 0;
}
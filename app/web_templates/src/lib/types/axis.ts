import type { AnyD3Scale } from '@visx/scale';
import type { Dimensions } from '@/lib/types/dimensions.ts';

export type AxisType = 'linear' | 'log' | 'category';

export type AxisSettingType = {
    show?: boolean;
    showLabel?: boolean;
    showTicks?: boolean;
    showGridLines?: boolean;
    type?: AxisType;
    label?: string;
    range?: {
        start: number;
        end: number;
    };
};

export type ChartAxisSettingsType = {
    x?: AxisSettingType;
    y?: AxisSettingType;
};

export type AxisScaleType = {
    scale: AnyD3Scale;
};

export interface AxesProps {
    dimensions: Dimensions;
    xAxis: AxisScaleType & AxisSettingType;
    yAxis: AxisScaleType & AxisSettingType;
    darkMode?: boolean;
}
import type { ScaleLinear, ScaleLogarithmic, ScaleOrdinal } from 'd3-scale';
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

export type DynamicScale = ScaleLinear<number, number, any> | ScaleLogarithmic<number, number, any> | ScaleOrdinal<string, number, any>;
export type AxisTicks = Array<string> | Array<number>;

export type AxisScaleType = {
    scale: DynamicScale;
    ticks: AxisTicks;
};

export interface AxesProps {
    dimensions: Dimensions;
    xAxis: AxisScaleType & AxisSettingType;
    yAxis: AxisScaleType & AxisSettingType;
    darkMode?: boolean;
};
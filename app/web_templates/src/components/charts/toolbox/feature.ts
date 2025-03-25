import type { EChartsType } from 'echarts';

export type ToolBoxFeature = 'save-as' | 'zoom' | 'restore';
export type ToolBoxFeatures = Array<ToolBoxFeature>;

export interface FeatureProps {
    chart: EChartsType | null;
}
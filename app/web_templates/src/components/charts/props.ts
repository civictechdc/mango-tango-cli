import type { Presenter } from '@/lib/data/presenters';
import type { DatasetOption, TopLevelFormatterParams } from "echarts/types/dist/shared";
import type { XAXisComponentOption, YAXisComponentOption } from "echarts/types/dist/echarts";

interface ChartContainerProps {
    presenter: Presenter;
}

interface ChartProps {
    data: DatasetOption | Array<DatasetOption>;
    tooltipFormatter?: (params: TopLevelFormatterParams) => string;
    axis?: {
        x?: XAXisComponentOption;
        y?: YAXisComponentOption;
    };
    seriesEncoding?: {
        x?: string | number;
        y?: string | number;
    };
    labels?: {
        x: string;
        y: string;
    };
}

export type { ChartContainerProps, ChartProps };
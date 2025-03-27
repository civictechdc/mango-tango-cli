import type { Presenter } from '@/lib/data/presenters';
import type {DatasetOption, TopLevelFormatterParams} from "echarts/types/dist/shared";

interface ChartContainerProps {
    presenter: Presenter;
}

interface ChartProps {
    data: DatasetOption | Array<DatasetOption>;
    tooltipFormatter?: (params: TopLevelFormatterParams) => string;
    labels?: {
        x: string;
        y: string;
    };
}

export type { ChartContainerProps, ChartProps };
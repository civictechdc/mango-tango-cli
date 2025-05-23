import type { Presenter } from '@/lib/data/presenters';
import type { AxisSettingType } from '@/lib/types/axis';
import type { Dimensions } from '@/lib/types/dimensions';
import type { TooltipFunction } from '@/lib/types/tooltip';

export interface ChartContainerProps {
    presenter: Presenter;
}

export interface ChartProps {
    data: Array<any>;
    tooltip: TooltipFunction<any>;
    dimensions?: Dimensions,
    darkMode?: boolean,
    axis?: {
        x?: AxisSettingType;
        y?: AxisSettingType;
    };
}

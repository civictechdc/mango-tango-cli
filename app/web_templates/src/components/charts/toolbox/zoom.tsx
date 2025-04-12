import { useEffect } from 'react';
import { ZoomIn, ZoomOut } from 'lucide-react';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip.tsx';
import type { ReactElement, FC } from 'react';
import type { EChartsCoreOption} from 'echarts/types/dist/echarts';
import type { FeatureProps } from '@/components/charts/toolbox/feature.ts';

export type ZoomAxisValue = {
    min: number;
    max: number;
};

export type ZoomHandlerValues = {
    x: ZoomAxisValue | null;
    y: ZoomAxisValue | null;
};

export type OnZoomFunctionType = (values: ZoomHandlerValues) => void;

export default function ZoomFeature({ chart }: FeatureProps): ReactElement<FC> {
    const itemClasses: string = 'grid items-center pl-1.5';
    const iconClasses: string = 'text-zinc-600 transition-colors cursor-pointer hover:text-cyan-600 dark:text-zinc-200';
    const iconWidth: string = '1.25rem';
    const iconHeight: string = '1.25rem';
    const handleZoomIn = (): void | undefined => chart?.dispatchAction({
        type: 'takeGlobalCursor',
        key: 'brush',
        brushOption: {
            brushType: 'rect',
            brushMode: 'single'
        }
    });
    const handleZoomOut = (): void | undefined => chart?.dispatchAction({
        type: 'dataZoom',
        batch: [
            {
                start: 0,
                end: 100
            }, {
                dataZoomIndex: 1,
                start: 0,
                end: 100
            }
        ]
    });
    const handleBrushEnd = (params: any): void => {
        if(chart == null) return;

        const options: EChartsCoreOption | undefined = chart?.getOption();

        if(options === undefined) return;

        const { areas } = params
        const { coordRange } = areas[0];

        chart.dispatchAction({
            type: 'dataZoom',
            batch: [
                {
                    startValue: coordRange[0][0],
                    endValue: coordRange[0][1]
                },
                {
                    dataZoomIndex: 1,
                    startValue: coordRange[1][0],
                    endValue: coordRange[1][1]
                }
            ]
        });
        chart.dispatchAction({
            type: 'brush',
            areas: []
        });
    };

    useEffect(() => {
        if(chart == null) return;

        chart.on('brushEnd', handleBrushEnd);

        return (): void => {
            if(chart == null) return;

            chart.off('brushEnd', handleBrushEnd);
        };
    }, [chart]);

    return (
        <TooltipProvider>
            <li className={itemClasses}>
                <Tooltip delayDuration={300}>
                    <TooltipTrigger asChild>
                        <button type="button" onClick={handleZoomIn}>
                            <ZoomIn width={iconWidth} height={iconHeight} className={iconClasses} />
                        </button>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p>Zoom In on Selection</p>
                    </TooltipContent>
                </Tooltip>
            </li>
            <li className={itemClasses}>
                <Tooltip delayDuration={300}>
                    <TooltipTrigger asChild>
                        <button type="button" onClick={handleZoomOut}>
                            <ZoomOut width={iconWidth} height={iconHeight} className={iconClasses} />
                        </button>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p>Zoom Reset</p>
                    </TooltipContent>
                </Tooltip>
            </li>
        </TooltipProvider>
    );
}
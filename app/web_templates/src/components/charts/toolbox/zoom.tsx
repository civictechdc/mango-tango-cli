import { ZoomIn, ZoomOut } from 'lucide-react';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip.tsx';
import type { ReactElement, FC } from 'react';
import type { ViewStateIncrementer } from '@/lib/types/zoom';

export interface ZoomFeatureProps {
    increment?: ViewStateIncrementer;
    decrement?: ViewStateIncrementer;
}

export default function ZoomFeature({ increment, decrement }: ZoomFeatureProps): ReactElement<FC> {
    const itemClasses: string = 'grid items-center pl-1.5';
    const iconClasses: string = 'text-zinc-600 transition-colors cursor-pointer hover:text-cyan-600 dark:text-zinc-200';
    const iconWidth: string = '1.25rem';
    const iconHeight: string = '1.25rem';

    return (
        <TooltipProvider>
            {increment && (
                <li className={itemClasses}>
                    <Tooltip delayDuration={300}>
                        <TooltipTrigger asChild>
                            <button type="button" onClick={(): void => increment()}>
                                <ZoomIn width={iconWidth} height={iconHeight} className={iconClasses} />
                            </button>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p>Increase Zoom</p>
                        </TooltipContent>
                    </Tooltip>
                </li>
            )}
            {decrement && (
                <li className={itemClasses}>
                    <Tooltip delayDuration={300}>
                        <TooltipTrigger asChild>
                            <button type="button" onClick={(): void => decrement()}>
                                <ZoomOut width={iconWidth} height={iconHeight} className={iconClasses} />
                            </button>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p>Decrease Zoom</p>
                        </TooltipContent>
                    </Tooltip>
                </li>
            )}
        </TooltipProvider>
    );
}
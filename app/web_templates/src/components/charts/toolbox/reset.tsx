import { RotateCcw } from 'lucide-react';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip.tsx';
import type { ReactElement, FC } from 'react';
import type { FeatureProps } from '@/components/charts/toolbox/feature.ts';

export default function ResetFeature({ chart }: FeatureProps): ReactElement<FC> {
    const handleClick = (): void => chart?.dispatchAction({type: 'restore'});

    return (
        <li className="grid items-center pl-1.5">
            <TooltipProvider>
                <Tooltip delayDuration={300}>
                    <TooltipTrigger asChild>
                        <button type="button" onClick={handleClick}>
                            <RotateCcw width="1.25rem" height="1.25rem" className="text-zinc-600 transition-colors cursor-pointer hover:text-cyan-600 dark:text-zinc-200" />
                        </button>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p>Restore</p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
        </li>
    );
}
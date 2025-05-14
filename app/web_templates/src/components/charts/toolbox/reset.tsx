import { RotateCcw } from 'lucide-react';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip.tsx';
import type { ReactElement, FC } from 'react';

export interface ResetFeatureProps {
    reset?: () => void;
}

export default function ResetFeature({ reset }: ResetFeatureProps): ReactElement<FC> {
    return (
        <TooltipProvider>
            {reset && (
                <li className="grid items-center pl-1.5">
                    <Tooltip delayDuration={300}>
                        <TooltipTrigger asChild>
                            <button type="button" onClick={(): void => reset()}>
                                <RotateCcw width="1.25rem" height="1.25rem" className="text-zinc-600 transition-colors cursor-pointer hover:text-cyan-600 dark:text-zinc-200" />
                            </button>
                        </TooltipTrigger>
                        <TooltipContent>
                            <p>Restore</p>
                        </TooltipContent>
                    </Tooltip>
                </li>
            )}
        </TooltipProvider>
    );
}
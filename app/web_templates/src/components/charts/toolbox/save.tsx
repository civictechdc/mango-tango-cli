import { Download } from 'lucide-react';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/components/ui/tooltip.tsx';
import type { ReactElement, FC } from 'react';
import type { FeatureProps } from '@/components/charts/toolbox/feature.ts';

export default function SaveAsFeature({ chart }: FeatureProps): ReactElement<FC> {
    const handleClick = (): void => {
        if(chart == null) return;

        const data: string = chart.getDataURL({type: 'png', backgroundColor: 'white'});

        if(data.length === 0) return;

        const now: Date = new Date();
        const elem: HTMLAnchorElement = document.createElement('a');

        elem.setAttribute('href', data);
        elem.setAttribute('target', '_blank');
        elem.setAttribute('download', `mango_tree_chart_download_${now.getFullYear()}${now.getMonth()}${now.getDate()}${now.getHours()}${now.getMinutes()}.png`);
        document.body.appendChild(elem);
        elem.dispatchEvent(new MouseEvent('click', {
            view: document.defaultView,
            bubbles: true,
            cancelable: false
        }));
        elem.remove();
    };

    return (
        <li className="grid items-center pl-1.5">
            <TooltipProvider>
                <Tooltip delayDuration={300}>
                    <TooltipTrigger asChild>
                        <button type="button" onClick={handleClick}>
                            <Download width="1.25rem" height="1.25rem" className="text-zinc-600 transition-colors cursor-pointer hover:text-cyan-600 dark:text-zinc-200" />
                        </button>
                    </TooltipTrigger>
                    <TooltipContent>
                        <p>Save as Image</p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
        </li>
    );
}
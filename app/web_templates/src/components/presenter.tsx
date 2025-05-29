import usePresentersState from '@/lib/state/presenters';
import NgramScatterPlot from '@/components/ngram_scatter.tsx';
import { Card, CardContent } from '@/components/ui/card.tsx';
import type { ReactElement, FC } from 'react';
import type { Presenter, PresenterCollection } from '@/lib/data/presenters';
import type { GlobalPresentersState } from '@/lib/state/presenters';

export default function PresenterView(): ReactElement<FC> {
    const presenters: PresenterCollection = usePresentersState((state: GlobalPresentersState) => state.presenters);
    const presenter: Presenter = presenters[0];

    let component: ReactElement<FC> | null = null;

    if(presenter) {
        if (presenter.figure_type === 'scatter') component = <NgramScatterPlot presenter={presenter} />;
    }

    return (
        <Card>
            <CardContent>
                {presenter ? component : <p>No charts to show yet!</p>}
            </CardContent>
        </Card>
    );
}
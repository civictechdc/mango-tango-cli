import usePresentersState from '@/lib/state/presenters';
import HistogramChart from '@/components/example_histogram.tsx';
import NgramScatterPlot from '@/components/ngram_scatter.tsx';
import TimeIntervalChart from '@/components/time_interval_bar_plot.tsx';
import { Card, CardContent } from '@/components/ui/card.tsx';
import type { ReactElement, FC } from 'react';
import type { Presenter, PresenterCollection } from '@/lib/data/presenters';
import type { GlobalPresentersState } from '@/lib/state/presenters';

export function PresenterView(): ReactElement<FC> {
    const presenters: PresenterCollection = usePresentersState((state: GlobalPresentersState) => state.presenters);

    if (presenters.length === 0) return <p>No charts to show yet!</p>;

    const presenter: Presenter = presenters[0];
    let component: ReactElement<FC> | null = null;

    if (presenter.figure_type === 'histogram') component = <HistogramChart presenter={presenter} />;
    if (presenter.figure_type === 'scatter') component = <NgramScatterPlot presenter={presenter} />;
    if(presenter.figure_type === 'bar') component = <TimeIntervalChart presenter={presenter} />;
    if(!component) component = <p>No component to show...</p>;

    return (
        <Card>
            <CardContent>{component}</CardContent>
        </Card>
    );
}
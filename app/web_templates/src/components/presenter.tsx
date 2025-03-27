import usePresentersState from '@/lib/state/presenters';
import HistogramChart from '@/components/example_histogram.tsx';
import NgramScatterPlot from '@/components/ngram_scatter.tsx';
import TimeIntervalChart from '@/components/time_interval_bar_plot.tsx';
import type { ReactElement, FC } from 'react';
import type { Presenter, PresenterCollection } from '@/lib/data/presenters';
import type { GlobalPresentersState } from '@/lib/state/presenters';

export function PresenterView(): ReactElement<FC> {
    const presenters: PresenterCollection = usePresentersState((state: GlobalPresentersState) => state.presenters);

    if (presenters.length === 0) return <p>No charts to show yet!</p>;

    const presenter: Presenter = presenters[0];

    if (presenter.figure_type === 'histogram') return <HistogramChart presenter={presenter} />;
    if (presenter.figure_type === 'scatter') return <NgramScatterPlot presenter={presenter} />;
    if(presenter.figure_type === 'bar') return <TimeIntervalChart presenter={presenter} />;

    return <p>No component to show...</p>;
}
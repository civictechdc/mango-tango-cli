import usePresentersState from '@/lib/state/presenters';
import HistogramChart from '@/components/example_histogram.tsx';
import ScatterPlotChart from '@/components/ngram_scatter.tsx';
import type { ReactElement, FC } from 'react';
import type { Presenter, PresenterCollection } from '@/lib/data/presenters';
import type { GlobalPresentersState } from '@/lib/state/presenters';

export function PresenterView(): ReactElement<FC> {
    const presenters: PresenterCollection = usePresentersState((state: GlobalPresentersState) => state.presenters);

    if (presenters.length === 0) return <p>No charts to show yet!</p>;

    const presenter: Presenter = presenters[0];
    let chartComponent: ReactElement<FC> | null = null;

    if (presenter.figure_type === 'histogram') chartComponent = <HistogramChart presenter={presenter} />;
    if (presenter.figure_type === 'scatter') chartComponent = <ScatterPlotChart presenter={presenter} />
    if (chartComponent  == null) return <p>No component to show...</p>;

    return chartComponent;
}
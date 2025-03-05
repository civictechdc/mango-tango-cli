import usePresentersState from '@/lib/state/presenters';
import type { ReactElement, FC, ReactNode } from 'react';
import type { Presenter, PresenterCollection } from '@/lib/data/presenters';
import type { GlobalPresentersState } from '@/lib/state/presenters';

export function PresenterView(): ReactElement<FC> {
    const presenters: PresenterCollection = usePresentersState((state: GlobalPresentersState) => state.presenters);
    console.log('PresenterView');
    if (presenters.length === 0) {
        return <p>No charts to show yet!</p>;
    }

    const presenter: Presenter = presenters[0];
    let chartComponent: ReactNode | null = null;

    if (presenter.figure_type === 'histogram') {
        chartComponent = <p>Test...</p>
    }

    return (
        <>{chartComponent}</>
    );
}
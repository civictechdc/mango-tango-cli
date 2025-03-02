import userPresentersState from '@/lib/state/presenters';
import type { ReactElement, FC } from 'react';
import type { Presenter, PresenterCollection } from '@/lib/data/presenters';
import type { GlobalPresentersState } from '@/lib/state/presenters';

export function PresenterView(): ReactElement<FC> {
    const presenters: PresenterCollection = userPresentersState((state: GlobalPresentersState) => state.presenters);

    if (presenters.length === 0) {
        return <p>No charts to show yet!</p>;
    }

    const presenter = presenters[0];

    return (
        <></>
    );
}
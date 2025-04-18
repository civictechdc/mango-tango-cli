import { create } from 'zustand';
import type { PresenterCollection } from '@/lib/data/presenters';

interface GlobalPresentersState {
    presenters: PresenterCollection;
    set: (presenters: PresenterCollection) => void;
    clear: () => void;
}

const usePresentersState = create<GlobalPresentersState>((setState): GlobalPresentersState => ({
    presenters: [],
    set: (presenters: PresenterCollection): void => setState((state: GlobalPresentersState): GlobalPresentersState => {
        state.presenters = presenters;

        return state;
    }),
    clear: (): void => setState((state: GlobalPresentersState): GlobalPresentersState => {
        state.presenters = [];

        return state;
    })
}));

export type { GlobalPresentersState };
export default usePresentersState;
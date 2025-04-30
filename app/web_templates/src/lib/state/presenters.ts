import { create } from 'zustand';
import type { PresenterCollection } from '@/lib/data/presenters';

interface GlobalPresentersState {
    presenters: PresenterCollection;
    set: (presenters: PresenterCollection) => void;
    clear: () => void;
}

const usePresentersState = create<GlobalPresentersState>((setState): GlobalPresentersState => ({
    presenters: [],
    set: (presenters: PresenterCollection): void => setState((state: GlobalPresentersState): GlobalPresentersState => ({
        ...state,
        presenters: presenters,
    })),
    clear: (): void => setState((state: GlobalPresentersState): GlobalPresentersState => ({
        ...state,
        presenters: [],
    }))
}));

export type { GlobalPresentersState };
export default usePresentersState;
import { create } from 'zustand';
import type { PresenterCollection } from '@/lib/data/presenters';

interface GlobalPresentersState {
    presenters: PresenterCollection;
    set: (presenters: PresenterCollection) => void;
    clear: () => void;
}

const userPresentersState = create<GlobalPresentersState>((setState) => ({
    presenters: [],
    set: (presenters: PresenterCollection) => setState((state: GlobalPresentersState) => {
        state.presenters = presenters;

        return state;
    }),
    clear: () => setState((state: GlobalPresentersState) => {
        state.presenters = [];

        return state;
    })
}));

export type { GlobalPresentersState };
export default userPresentersState;
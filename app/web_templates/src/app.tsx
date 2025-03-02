import { useEffect, useState } from 'react';
import { RouterProvider, createRouter, createRootRoute, createRoute, createBrowserHistory } from '@tanstack/react-router';
import {fetchPresenters} from '@/lib/data/presenters.ts';
import userPresentersState from '@/lib/state/presenters.ts';
import type { ReactElement, FC, PropsWithChildren } from 'react';
import type { Router } from '@tanstack/react-router';
import type { PresenterCollection } from '@/lib/data/presenters';
import type { GlobalPresentersState } from '@/lib/state/presenters';

function RootParent({ children }: PropsWithChildren): ReactElement<FC> {
    return <>{children}</>;
}

const rootRoute = createRootRoute({
    component: () => <RootParent />
});

export default function App(): ReactElement<FC> {
    const set = userPresentersState((state: GlobalPresentersState) => state.set);
    const [routes, setRoutes] = useState<Router<any, any, any>["routeTree"] | null>(null);

    useEffect(() => {
        const controller = new AbortController();

        (async (): Promise<void> => {
            const presenters = await fetchPresenters(controller.signal) as PresenterCollection;

            setRoutes(createRouter({
                routeTree: createRoute({
                    path: '/',
                    getParentRoute: () => rootRoute,
                    component: () => <></>
                }),
                history: createBrowserHistory(),
            }));
            set(presenters);
        })();

        return () => {
            controller.abort();
        };
    }, []);

    return <RouterProvider router={routes} />;
}
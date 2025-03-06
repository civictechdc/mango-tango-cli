import { useEffect, useState } from 'react';
import { fetchPresenters } from '@/lib/data/presenters.ts';
import userPresentersState from '@/lib/state/presenters.ts';
import {
    RouterProvider,
    createRouter,
    createRootRoute,
    createRoute,
    createBrowserHistory,
    Outlet
} from '@tanstack/react-router';
import { PresenterView } from '@/components/presenter.tsx';
import type { ReactElement, FC } from 'react';
import type { Router } from '@tanstack/react-router';
import type { PresenterCollection } from '@/lib/data/presenters';
import type { GlobalPresentersState } from '@/lib/state/presenters';

function RootParent(): ReactElement<FC> {
    return <Outlet />;
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

            const indexRoute = createRoute({
                path: '/',
                getParentRoute: () => rootRoute,
                component: () => <PresenterView />,
                ssr: false
            });


            setRoutes(createRouter({
                routeTree: rootRoute.addChildren([indexRoute]),
                history: createBrowserHistory(),
            }));
            set(presenters);
        })();

        return () => {
            controller.abort();
        }
    }, []);

    if (!routes) {
        return <p>loading...</p>;
    }

    return <RouterProvider  router={routes} />;
}
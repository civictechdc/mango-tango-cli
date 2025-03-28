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
import { ThemeProvider } from '@/components/theme-provider.tsx';
import DarkModeToggle from '@/components/dark-mode-toggle.tsx';
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

    return (
        <ThemeProvider defaultTheme="system">
            <header className="grid grid-flow-col row-span-1 justify-between items-center">
                <h1><span className="font-bold pr-1">Project Name:</span> {window.PROJECT_NAME}</h1>
                <img
                    width="100"
                    height="100"
                    src="data:image/png;base64,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"
                    alt="logo" />
            </header>
            <main className="grid grid-flow-col justify-center items-center">
                {routes ? <RouterProvider router={routes}/> : <p>loading...</p>}
            </main>
            <footer className="grid grid-flow-col row-span-1 justify-end items-center">
                <DarkModeToggle />
            </footer>
        </ThemeProvider>

    );
}
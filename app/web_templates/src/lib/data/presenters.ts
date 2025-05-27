import type {
    Presenter,
    PresenterCollection,
    PresenterQueryParams,
    PresenterResponse,
    PresentersResponse
} from '@/lib/types/presenters.ts';

export async function fetchPresenters(signal?: AbortSignal, queryParams?: PresenterQueryParams): Promise<PresenterCollection | null> {
    let url: string = 'http://localhost:8050/api/presenters';
    let fetchConf: RequestInit = {
        method: 'GET'
    };

    if (signal) fetchConf.signal = signal;
    if (queryParams) url += `?${new URLSearchParams(queryParams).toString()}`;

    const response: Response = await fetch(url, fetchConf);

    if (!response.ok) return null;

    const presenters = await response.json() as PresentersResponse;

    return presenters.data;
}

export async function fetchPresenter<PresenterType extends Presenter>(id: string, signal?: AbortSignal, queryParams?: PresenterQueryParams): Promise<PresenterType | null> {
    if(id.length === 0) return null;

    let url: string = `http://localhost:8050/api/presenters/${id}`;
    let fetchConf: RequestInit = {
        method: 'GET'
    };

    if (signal) fetchConf.signal = signal;
    if (queryParams) url += `?${new URLSearchParams(queryParams).toString()}`;

    const response: Response = await fetch(url, fetchConf);

    if (!response.ok) return null;

    const presenter = await response.json() as PresenterResponse<PresenterType>;

    return presenter.data;
}
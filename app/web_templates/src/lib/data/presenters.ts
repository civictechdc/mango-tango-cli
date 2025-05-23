export type DependencyOutputColumn = {
    data_type: string;
    description: string | null;
    human_readable_name: string | null;
    name: string;
};

export type DependencyAnalyzerInput = {
    columns: Array<{
        data_type: string;
        description: string | null;
        human_readable_name: string | null;
        name: string;
        name_hints: Array<string>;
    }>;
};

export type DependencyOutput = {
    columns: Array<DependencyOutputColumn>;
    description: string | null;
    id: string;
    internal: boolean;
    name: string;
};

export type DependencyAnalyzer = {
    id: string;
    input: DependencyAnalyzerInput;
    kind: string;
    long_description: string | null;
    name: string;
    outputs: Array<DependencyOutput>;
    short_description: string | null;
    version: string;
};

export type PresenterDependecy = {
    base_analyzer: DependencyAnalyzer;
    depends_on: Array<PresenterDependecy>;
    id: string;
    kind: string;
    long_description: string | null;
    name: string;
    outputs: Array<DependencyOutput>;
    short_description: string | null;
    version: string;
};

export type PresenterAxisLabel = {
    label: string;
    value: string;
};

export type PresenterAxisData = {
    [index: string]: Array<number>;
};

export type Presenter = {
    axis: {
        x: PresenterAxisLabel;
        y: PresenterAxisLabel;
    },
    depends_on: Array<PresenterDependecy>;
    explanation: {
        [index: string]: string;
    };
    figure_type: 'histogram' | 'scatter' | 'bar';
    id: string;
    kind: string;
    long_description: string | null;
    name: string;
    server_name: string | null;
    short_description: string | null;
    version: string;
    ngrams: Array<string> | undefined;
    message_data: (string | number)[][] | undefined;
    x: Array<string> | Array<number> | PresenterAxisData;
    y: Array<string> | Array<number> | PresenterAxisData;
};

export type PresenterCollection = Array<Presenter>;

export type PresentersResponse = {
    code: number;
    count: number;
    data: PresenterCollection;
};

export async function fetchPresenters(signal: AbortSignal | undefined): Promise<PresenterCollection | null> {
    let fetchConf: RequestInit = {
        method: 'GET'
    };

    if (signal !== undefined) fetchConf.signal = signal;

    const response: Response = await fetch(`http://localhost:8050/api/presenters`, fetchConf);

    if (!response.ok) {
        return null;
    }

    const presenters = await response.json() as PresentersResponse;

    return presenters.data;
}
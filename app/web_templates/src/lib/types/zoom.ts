
export type ViewStateIncrementer = (step?: number) => void;
export type ChartViewStateHooks = {
    increment: ViewStateIncrementer;
    decrement: ViewStateIncrementer;
    reset: () => void;
};
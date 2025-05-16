
export type TooltipContent = string | {
    text?: string
    html?: string
    className?: string
    style?: Partial<CSSStyleDeclaration>
} | null;

export type TooltipFunction<T> = (datapoint: T) => string;
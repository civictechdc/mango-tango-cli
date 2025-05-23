
export type CoordinateType = string | number;

export type DataPoint = {
    x: CoordinateType;
    y: CoordinateType;
};

export type ChartDataPoint<T> = T & {
    position: Array<CoordinateType>;
    color: Array<number>;
};

export type ChartDataPoints<T> = Array<ChartDataPoint<T>>;
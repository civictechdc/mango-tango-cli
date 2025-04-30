import { format } from 'd3-format';
import { isOrdinalScale } from '@/lib/axis';
import type { ReactElement, FC } from 'react';
import type { AxisType, AxesProps } from '@/lib/types/axis';

export default function ChartAxes({ dimensions, xAxis, yAxis, darkMode = true }: AxesProps): ReactElement<FC> {
    const textColor = darkMode ? '#ffffff' : '#000000';
    const gridColor = darkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)';
    const leftAxisX = dimensions.margins?.left || 80;
    const bottomAxisY = dimensions.height - (dimensions.margins?.bottom || 80);
    const rightAxisX = dimensions.width - (dimensions.margins?.right || 60);
    const topAxisY = dimensions.margins?.top || 60;
    const formatTick = (value: string | number, scaleType: AxisType): string => {
        if(scaleType === 'category') return value as string;
        if(scaleType === 'log') return format(".1~s")(value as number);
        return format(",.1f")(value as number);
    };

    console.log('xAxis:', xAxis);
    console.log('yAxis:', xAxis);

    return (
        <svg
            width={dimensions.width}
            height={dimensions.height}
            style={{
                position: 'absolute',
                top: 0,
                left: 0,
                pointerEvents: 'none',
                fontFamily: 'sans-serif',
                fontSize: '12px',
                zIndex: -1
            }}
        >
            {/* X and Y axis lines */}
            <line
                x1={leftAxisX}
                y1={bottomAxisY}
                x2={rightAxisX}
                y2={bottomAxisY}
                stroke={textColor}
                strokeWidth={1.5}
            />
            <line
                x1={leftAxisX}
                y1={bottomAxisY}
                x2={leftAxisX}
                y2={topAxisY}
                stroke={textColor}
                strokeWidth={1.5}
            />

            {/* Y-axis ticks and grid lines */}
            {yAxis.ticks.map((tick, i) => {
                if (!yAxis.scale) return null;

                const tickValue = isOrdinalScale(yAxis.scale)
                    ? yAxis.scale(tick as string)
                    : yAxis.scale(tick as number);

                return (
                    <g key={`y-tick-${tick}-${i}`}>
                        {/* Grid line */}
                        {(yAxis.showGridLines !== false && i > 0) && (
                            <line
                                x1={leftAxisX}
                                y1={tickValue}
                                x2={rightAxisX}
                                y2={tickValue}
                                stroke={gridColor}
                                strokeWidth={1}
                            />
                        )}

                        {/* Tick mark */}
                        <line
                            x1={leftAxisX - 5}
                            y1={tickValue}
                            x2={leftAxisX - 2}
                            y2={tickValue}
                            stroke={textColor}
                            strokeWidth={1}
                        />

                        {/* Tick label */}
                        <text
                            x={leftAxisX - 10}
                            y={tickValue}
                            textAnchor="end"
                            dominantBaseline="middle"
                            fill={textColor}
                            fontSize="12px"
                        >
                            {formatTick(tick, yAxis.type)}
                        </text>
                    </g>
                );
            })}

            {xAxis.ticks.map((tick, i) => {
                if (!xAxis.scale) return null;

                const tickValue = isOrdinalScale(xAxis.scale)
                    ? xAxis.scale(tick as string)
                    : xAxis.scale(tick as number);

                return (
                    <g key={`x-tick-${tick}-${i}`}>
                        {/* Grid line */}
                        {(xAxis.showGridLines !== false && i > 0) && (
                            <line
                                x1={tickValue}
                                y1={topAxisY}
                                x2={tickValue}
                                y2={bottomAxisY}
                                stroke={gridColor}
                                strokeWidth={1}
                            />
                        )}

                        {/* Tick mark */}
                        <line
                            x1={tickValue}
                            y1={bottomAxisY+2}
                            x2={tickValue}
                            y2={bottomAxisY+5}
                            stroke={textColor}
                            strokeWidth={1}
                        />

                        {/* Tick label */}
                        <text
                            x={tickValue}
                            y={bottomAxisY + 20}
                            textAnchor="middle"
                            fill={textColor}
                            fontSize="12px"
                        >
                            {formatTick(tick, xAxis.type)}
                        </text>
                    </g>
                );
            })}

            {/* Axis labels */}
            {xAxis.label && (
                <text
                    x={dimensions.width / 2}
                    y={dimensions.height - 15}
                    textAnchor="middle"
                    fill={textColor}
                    fontSize="14px"
                >
                    {xAxis.label}
                </text>
            )}

            {yAxis.label && (
                <text
                    x={15}
                    y={dimensions.height / 2}
                    textAnchor="middle"
                    transform={`rotate(-90, 15, ${dimensions.height / 2})`}
                    fill={textColor}
                    fontSize="14px"
                >
                    {yAxis.label}
                </text>
            )}
        </svg>
    );
}

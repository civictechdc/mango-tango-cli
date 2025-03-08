import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent } from '@/components/ui/chart.tsx';
import type { ReactElement, FC } from 'react';
import type { ChartProps } from '@/components/charts/props.ts';

type HistogramBin = {
    binStart: number;
    binEnd: number;
    count: number;
    label: string;
};

export default function HistogramChart({ presenter }: ChartProps): ReactElement<FC> {
    const data: Array<HistogramBin> = useMemo(() => {
        if (presenter == null) return [];

        const rawData = presenter.x as Array<number>;
        const binCount = 50;
        const maxValue = Math.max(...rawData);
        const binWidth = maxValue / binCount;
        const bins: Array<HistogramBin> = Array.from({length: binCount}, (_, index: number): HistogramBin => {
            const binStart = maxValue + index * binWidth;
            const binEnd = binStart + binWidth;

            return {
                binStart: binStart,
                binEnd: binEnd,
                count: 0,
                label: `${Math.floor(binStart)} - ${Math.floor(binEnd)}`,
            };
        });

        for (const value of rawData) {
            if (value > maxValue) continue;

            const binIndex = Math.min(Math.floor(value / binWidth), binCount - 1);

            if (binIndex >= 0 && binIndex < bins.length) bins[binIndex].count++;
        }

        return bins;
    }, [presenter]);

    console.log(data);

    return (
        <ChartContainer config={{}}>
            <BarChart accessibilityLayer data={data}>
                <XAxis
                  dataKey="bin"
                  tickLine={false}
                  tickMargin={10}
                  axisLine={false}
                  label={{
                    value: presenter.axis.x.label,
                    position: 'bottom',
                    offset: 0,
                    style: { textAnchor: 'middle' }
                  }}
                />
                <YAxis tickLine={false}
                  tickMargin={10}
                  axisLine={false}
                  label={{
                    value: presenter.axis.y.label,
                    angle: -90,
                    position: 'left',
                    offset: -1,
                    style: { textAnchor: 'middle' }
                  }}
                />
                <CartesianGrid vertical={false} />
                <ChartTooltip content={<ChartTooltipContent />} />
                <ChartLegend content={<ChartLegendContent />} />
                <Bar dataKey="count" fill="#2563eb" name={presenter.axis.y.label} radius={4} />
            </BarChart>
        </ChartContainer>
    );
}

export type { HistogramBin };
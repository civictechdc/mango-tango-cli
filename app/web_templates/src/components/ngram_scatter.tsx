import { useMemo } from 'react';
import { ScatterChart, Scatter,  XAxis, YAxis, CartesianGrid } from 'recharts';
import { ChartContainer, ChartTooltip, ChartLegend, ChartLegendContent } from '@/components/ui/chart.tsx';
import type { ReactElement, FC } from 'react';
import type { ChartProps } from '@/components/charts/props.ts';
import type { PresenterAxisData } from '@/lib/data/presenters.ts';

export type ScatterPlotData = {
    ngram: string;
    x: number;
    y: number;
}

export default function ScatterPlotChart({ presenter }: ChartProps): ReactElement<FC> {
    const data: Array<ScatterPlotData> = useMemo(() => {
        if (presenter == null) return [];

        const rawNgrams = presenter.ngrams as Array<string>;
        const rawX = presenter.x as Array<number>;
        const rawY = (presenter.y as PresenterAxisData)['total_repetition'] as Array<number>;

        return Array.from({length: rawX.length}, (_, index: number): ScatterPlotData => ({
            ngram: rawNgrams[index],
            x: rawX[index],
            y: rawY[index],
        })).filter(item => item.x > 0 && item.y > 0);
    }, [presenter]);

    return (
        <ChartContainer config={{}}>
            <ScatterChart>
                <XAxis
                  type="number"
                  name="User Count"
                  dataKey="x"
                  tickLine={false}
                  tickMargin={10}
                  axisLine={false}
                  domain={['auto', 'auto']}
                  scale="log"
                  tickFormatter={(value) => value.toLocaleString()}
                  label={{
                    value: presenter.axis.x.label,
                    position: 'bottom',
                    offset: 0,
                    style: { textAnchor: 'middle' }
                  }}
                />
                <YAxis
                  type="number"
                  name="Total Repetition"
                  dataKey="y"
                  tickLine={false}
                  tickMargin={10}
                  axisLine={false}
                  domain={['auto', 'auto']}
                  scale="log"
                  tickFormatter={(value) => value.toLocaleString()}
                  label={{
                    value: presenter.axis.y.label,
                    angle: -90,
                    position: 'left',
                    offset: -1,
                    style: { textAnchor: 'middle' }
                  }}
                />
                <CartesianGrid vertical={false} />
                <ChartTooltip
                    formatter={(value: number, name: string) => [value.toLocaleString(), name]}
                    labelFormatter={(value) => `N-gram: ${value}`}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-white p-2 border border-gray-200 shadow-md rounded">
                            <p className="font-bold">{`"${data.ngram}"`}</p>
                            <p>{`User Count: ${data.x.toLocaleString()}`}</p>
                            <p>{`Total Repetition: ${data.y.toLocaleString()}`}</p>
                          </div>
                        );
                      }
                      return null;
                    }} />
                <ChartLegend content={<ChartLegendContent />} />
                <Scatter name="N-gram Repetition" data={data} line={false} />
            </ScatterChart>
        </ChartContainer>
    );
}
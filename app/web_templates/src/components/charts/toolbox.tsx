import { useMemo } from 'react';
import SaveAsFeature from '@/components/charts/toolbox/save.tsx';
import ZoomFeature from '@/components/charts/toolbox/zoom.tsx';
import ResetFeature from '@/components/charts/toolbox/reset.tsx';
import type { ReactElement, FC } from 'react';
import type { EChartsType } from 'echarts';
import type { ToolBoxFeature, ToolBoxFeatures } from '@/components/charts/toolbox/feature.ts';

export interface ToolBoxProps {
    features: ToolBoxFeatures;
    chart: EChartsType | null;
}

type ComponentArray = Array<ReactElement<FC>>;

export default function ToolBox({ features, chart }: ToolBoxProps): ReactElement<FC> {
    const components = useMemo<ComponentArray>(() => {
        const addedFeatures: ToolBoxFeatures = [];

        return features.reduce((accumValue: ComponentArray, currentFeature: ToolBoxFeature): ComponentArray => {
            if(addedFeatures.includes(currentFeature)) return accumValue;

            const key: string = `toolbox-feature-${addedFeatures.length}`;

            if(currentFeature === 'save-as') accumValue.push(<SaveAsFeature key={key} chart={chart} />);
            if(currentFeature === 'zoom') accumValue.push(<ZoomFeature key={key} chart={chart} />);
            if(currentFeature === 'restore') accumValue.push(<ResetFeature key={key} chart={chart} />);

            addedFeatures.push(currentFeature);

            return accumValue;
        }, []);
    }, [features, chart]);

    return <ul className="grid auto-cols-max grid-flow-col items-center justify-end">{components}</ul>;
}
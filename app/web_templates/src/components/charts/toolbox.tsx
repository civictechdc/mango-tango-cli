import { useMemo } from 'react';
import SaveAsFeature from '@/components/charts/toolbox/save.tsx';
import ZoomFeature from '@/components/charts/toolbox/zoom.tsx';
import ResetFeature from '@/components/charts/toolbox/reset.tsx';
import type { ReactElement, FC } from 'react';
import type { ToolBoxFeature, ToolBoxFeatures } from '@/components/charts/toolbox/feature.ts';
import type { ViewStateIncrementer } from '@/lib/types/zoom';

export interface ToolBoxProps {
    features: ToolBoxFeatures;
    zoomIncrement?: ViewStateIncrementer;
    zoomDecrement?: ViewStateIncrementer;
    zoomReset?: () => void;
}

type ComponentArray = Array<ReactElement<FC>>;

export default function ToolBox({ features, zoomIncrement, zoomDecrement, zoomReset }: ToolBoxProps): ReactElement<FC> {
    const components = useMemo<ComponentArray>(() => {
        const addedFeatures: ToolBoxFeatures = [];

        return features.reduce((accumValue: ComponentArray, currentFeature: ToolBoxFeature): ComponentArray => {
            if(addedFeatures.includes(currentFeature)) return accumValue;

            const key: string = `toolbox-feature-${addedFeatures.length}`;

            if(currentFeature === 'save-as') accumValue.push(<SaveAsFeature key={key} />);
            if(currentFeature === 'zoom') accumValue.push(<ZoomFeature key={key} increment={zoomIncrement} decrement={zoomDecrement} />);
            if(currentFeature === 'restore') accumValue.push(<ResetFeature key={key} reset={zoomReset} />);

            addedFeatures.push(currentFeature);

            return accumValue;
        }, []);
    }, [features]);

    return <ul className="grid auto-cols-max grid-flow-col items-center">{components}</ul>;
}
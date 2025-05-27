import { useMemo, useCallback } from 'react';
import {DataEditor, GridCellKind} from '@glideapps/glide-data-grid';
import type { ReactElement, FC } from 'react';
import type { GridColumn, Item, GridCell, Theme } from '@glideapps/glide-data-grid';
import type { CoordinateType } from '@/lib/types/datapoint.ts';

import '@glideapps/glide-data-grid/dist/index.css';

export interface BaseRow {
    [index: string]: any;
    x: CoordinateType;
    y: CoordinateType;
}

export interface DataTableProps<RowType extends BaseRow> {
    columns: Array<GridColumn>;
    data: Array<RowType>;
    darkMode?: boolean;
    theme?: Partial<Theme>;
}

export default function DataTable<RowType extends BaseRow>({ data, columns, theme, darkMode }: DataTableProps<RowType>): ReactElement<FC> {
    const mainTheme = useMemo<Partial<Theme>>(() => {
        if(theme != null) return theme;
        if(darkMode) return {
            accentColor: "#8c96ff",
            accentLight: "rgba(202, 206, 255, 0.253)",
            textDark: "#ffffff",
            textMedium: "#b8b8b8",
            textLight: "#a0a0a0",
            textBubble: "#ffffff",
            bgIconHeader: "#b8b8b8",
            fgIconHeader: "#000000",
            textHeader: "#a1a1a1",
            textHeaderSelected: "#000000",
            bgCell: "#16161b",
            bgCellMedium: "#202027",
            bgHeader: "#212121",
            bgHeaderHasFocus: "#474747",
            bgHeaderHovered: "#404040",
            bgBubble: "#212121",
            bgBubbleSelected: "#000000",
            bgSearchResult: "#423c24",
            borderColor: "rgba(225,225,225,0.2)",
            drilldownBorder: "rgba(225,225,225,0.4)",
            linkColor: "#4F5DFF",
            headerFontStyle: "bold 14px",
            baseFontStyle: "13px",
            fontFamily: "Inter, Roboto, -apple-system, BlinkMacSystemFont, avenir next, avenir, segoe ui, helvetica neue, helvetica, Ubuntu, noto, arial, sans-serif"
        };

        return {};
    }, [theme, darkMode]);
    const columnsIndexes = useMemo<Array<string>>(() =>
        columns.reduce<Array<string>>((accumValue: Array<string>, currentValue: GridColumn): Array<string> => {
            if(currentValue.id == null || currentValue.id?.length === 0) return accumValue;

            accumValue.push(currentValue.id);
            return accumValue;
        }, new Array<string>())
    , [columns]);
    const getCellContent = useCallback(([column, row]: Item): GridCell => {
        const dataRow: RowType = data[row];
        const item: any = dataRow[columnsIndexes[column]];
        let cellType: GridCellKind = GridCellKind.Text;

        if(typeof item === 'number') cellType = GridCellKind.Number;
        if(typeof item === 'boolean') cellType = GridCellKind.Boolean;

        return {
            kind: cellType,
            allowOverlay: false,
            displayData: `${item}`,
            data: item
        };
    }, [columnsIndexes]);

    return <DataEditor
                scaleToRem
                width="100%"
                height="50rem"
                className="rounded-md border border-zinc-200 dark:border-zinc-800 shadow-md"
                columns={columns}
                getCellContent={getCellContent}
                theme={mainTheme}
                rows={data.length} />;
}
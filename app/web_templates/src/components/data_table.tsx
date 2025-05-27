import { useMemo, useCallback, useState } from 'react';
import {CompactSelection , DataEditor, GridCellKind } from '@glideapps/glide-data-grid';
import type { ReactElement, FC } from 'react';
import type { GridColumn, Item, GridCell, Theme, GridSelection } from '@glideapps/glide-data-grid';
import type { CoordinateType } from '@/lib/types/datapoint.ts';
import '@glideapps/glide-data-grid/dist/index.css';

export type ColumnsAlignmentProperties = {
    [index: string]: 'left' | 'center' | 'right';
};

export interface BaseRow {
    [index: string]: any;
    x: CoordinateType;
    y: CoordinateType;
}

export interface DataTableProps<RowType extends BaseRow> {
    columns: Array<GridColumn>;
    data: Array<RowType>;
    onSelect?: (item: RowType | null) => void;
    darkMode?: boolean;
    theme?: Partial<Theme>;
    columnContentAlignment?: ColumnsAlignmentProperties;
}

export default function DataTable<RowType extends BaseRow>({
   data,
   columns,
   theme,
   darkMode,
   onSelect,
   columnContentAlignment
}: DataTableProps<RowType>): ReactElement<FC> {
    const [gridSelection, setGridSelection] = useState<GridSelection>({
        columns: CompactSelection.empty(),
        rows: CompactSelection.empty(),
    });
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
        const index: string = columnsIndexes[column];
        const item: any = dataRow[index];
        let cellType: GridCellKind = GridCellKind.Text;

        if(typeof item === 'number') cellType = GridCellKind.Number;
        if(typeof item === 'boolean') cellType = GridCellKind.Boolean;

        if(columnContentAlignment && columnContentAlignment[index]) return {
            kind: cellType,
            allowOverlay: false,
            displayData: `${item}`,
            data: item,
            contentAlign: columnContentAlignment[index]
        };

        return {
            kind: cellType,
            allowOverlay: false,
            displayData: `${item}`,
            data: item
        };
    }, [columnsIndexes, data]);
    const onGridSelection = useCallback((selectionChange: GridSelection): void => {
        setGridSelection(selectionChange);
        console.log(selectionChange);
        const row: number | undefined = selectionChange.rows.first();
        const item: RowType | null = row != null ? data[row] : null;

        if(onSelect) onSelect(item);
    }, []);

    return <DataEditor
                scaleToRem
                width="100%"
                height="50rem"
                className="rounded-md border border-zinc-200 dark:border-zinc-800 shadow-md"
                rowSelect="single"
                rowMarkers="checkbox-visible"
                columns={columns}
                gridSelection={gridSelection}
                getCellContent={getCellContent}
                onGridSelectionChange={onGridSelection}
                theme={mainTheme}
                rows={data.length} />;
}
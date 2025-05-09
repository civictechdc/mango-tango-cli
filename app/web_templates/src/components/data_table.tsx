import { useRef, useMemo, useState } from 'react';
import { flexRender, getCoreRowModel, getSortedRowModel, useReactTable, getPaginationRowModel } from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Table, TableBody, TableHeader, TableHead, TableRow, TableCell } from '@/components/ui/table';
import type { ReactElement, FC } from 'react';
import type { ColumnDef, Row } from '@tanstack/react-table';
import type { VirtualItem } from '@tanstack/react-virtual';

export interface DataTableProps {
    columns: Array<ColumnDef<any>>;
    data: Array<{[index: string]: any;}>;
}

export default function DataTable({ data, columns }: DataTableProps): ReactElement<FC> {
    const tableRef = useRef<HTMLDivElement>(null);
    const columnDefinitions = useMemo<Array<ColumnDef<any>>>(() => columns, []);
    const [pagination, setPagination] = useState({
      pageIndex: 0, //initial page index
      pageSize: 50, //default page size
    });
    const table = useReactTable({
        data: data,
        columns: columnDefinitions,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getPaginationRowModel: getPaginationRowModel(),
        onPaginationChange: setPagination, //update the pagination state when internal APIs mutate the pagination state
          state: {
            //...
            pagination,
          },
        debugTable: true,
    });

    const { rows } = table.getRowModel();
    const rowVirtualizer = useVirtualizer<HTMLDivElement, HTMLTableRowElement>({
        count: rows.length,
        estimateSize: () => 33,
        getScrollElement: () => tableRef.current,
        measureElement:
            typeof window !== 'undefined' &&
            navigator.userAgent.indexOf('Firefox') === -1
                ? element => element?.getBoundingClientRect().height
                : undefined,
        overscan: 5,
    });


    return (
        <div>
        <Table ref={tableRef} containerHeight={800} className="grid">
            <TableHeader className="grid sticky top-0 z-10 dark:bg-zinc-950">
                {table.getHeaderGroups().map((headerGroup) => (
                    <TableRow key={headerGroup.id} className="flex w-full">
                        {headerGroup.headers.map((header) => {
                            return (
                                <TableHead key={header.id} className="flex items-center" style={{width: header.getSize()}}>
                                    {header.isPlaceholder
                                        ? null
                                        : flexRender(
                                            header.column.columnDef.header,
                                            header.getContext()
                                        )}
                                </TableHead>
                            )
                        })}
                    </TableRow>
                ))}
            </TableHeader>
            <TableBody className="grid relative" style={{height: `${rowVirtualizer.getTotalSize()}px`}}>
                {rowVirtualizer.getVirtualItems().map((virtualRow: VirtualItem) => {
                    const row = rows[virtualRow.index] as Row<any>;

                    return (
                       <TableRow
                           data-index={virtualRow.index}
                            ref={(node: HTMLTableRowElement) => rowVirtualizer.measureElement(node)}
                            key={row.id}
                            className="flex absolute w-full"
                            style={{
                                transform: `translateY(${virtualRow.start}px)`
                            }}>
                           {row.getVisibleCells().map(cell => {
                               return (
                                   <TableCell
                                       key={cell.id}
                                       className="flex"
                                       style={{
                                           width: cell.column.getSize(),
                                       }}
                                   >
                                       {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                   </TableCell>
                               )
                           })}
                       </TableRow>
                    )
                })}
            </TableBody>
        </Table>
        <div>
              <button type="button" className="btn btn-outline-dark" onClick={() => table.firstPage()} disabled={!table.getCanPreviousPage()}>
                        {'<<'}
              </button>
              <button onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>
                        {'<'}
              </button>
              <select value={table.getState().pagination.pageIndex}
                  onChange={e => {
                    table.setPageIndex(Number(e.target.value))
                  }}>
                  {Array.from({length: table.getPageCount()}, (_, i) => i).map(pageNum => (
                    <option key={pageNum} value={pageNum}>
                      {pageNum+1}
                    </option>
                  ))}
              </select>
              <button onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>
                    {'>'}
              </button>
              <button onClick={() => table.lastPage()} disabled={!table.getCanNextPage()}>
                    {'>>'}
              </button>
              <select
                  value={table.getState().pagination.pageSize}
                  onChange={e => {
                    table.setPageSize(Number(e.target.value))
                  }}
                >
                  {[10, 50, 100, 150].map(pageSize => (
                    <option key={pageSize} value={pageSize}>
                      {pageSize}
                    </option>
                  ))}
              </select>
        </div>
    </div>

    );

}
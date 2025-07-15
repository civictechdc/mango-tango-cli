import { useState } from 'react';
import { clsx } from 'clsx';
import { createDownloadLink } from '@/lib/data/download';
import { Button } from '@/components/ui/button';
import { Sheet, Table, Braces, ChevronDown } from 'lucide-react';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/components/ui/dropdown-menu';
import type { ReactElement, FC, PropsWithChildren } from 'react';
import type { PresenterQueryParams } from '@/lib/types/presenters';
import type { DownloadFileType } from '@/lib/types/download';

export interface DownloadButtonProps {
    presenterID: string;
    queryParams?: PresenterQueryParams;
}

export interface DownloadLinkProps extends PropsWithChildren {
    presenterID: string;
    fileType: DownloadFileType;
    queryParams?: PresenterQueryParams;
}

export function DownloadDatasetLink({ presenterID, fileType, queryParams, children }: DownloadLinkProps): ReactElement<FC> {
    return (
        <a target="_blank"
           href={createDownloadLink(presenterID, fileType, queryParams)}
           className="inline-flex items-center w-full">
            {children}
        </a>
    );
}

export function DownloadDatasetButton({ presenterID, queryParams }: DownloadButtonProps): ReactElement<FC> {
    const [open, setOpen] = useState<boolean>(false);
    const handleToggle = (value: boolean): void => setOpen(value);
    const chevronClasses = clsx('transition-transform', {
        'rotate-180': open
    });

    return (
        <DropdownMenu open={open} onOpenChange={handleToggle}>
            <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                    Export
                    <ChevronDown className={chevronClasses} />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-20" align="end">
                <DropdownMenuItem>
                    <DownloadDatasetLink fileType="excel" presenterID={presenterID} queryParams={queryParams}>
                        <Sheet className="mr-1" />
                        <span className="font-bold">Excel</span>
                    </DownloadDatasetLink>
                </DropdownMenuItem>
                <DropdownMenuItem>
                    <DownloadDatasetLink fileType="json" presenterID={presenterID} queryParams={queryParams}>
                        <Braces className="mr-1" />
                        <span className="font-bold">JSON</span>
                    </DownloadDatasetLink>
                </DropdownMenuItem>
                <DropdownMenuItem>
                    <DownloadDatasetLink fileType="csv" presenterID={presenterID} queryParams={queryParams}>
                        <Table className="mr-1" />
                        <span className="font-bold">CSV</span>
                    </DownloadDatasetLink>
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
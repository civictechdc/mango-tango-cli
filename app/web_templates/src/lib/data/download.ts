import type { DownloadFileType } from '@/lib/types/download';
import type { PresenterQueryParams } from '@/lib/types/presenters';

export function createDownloadLink(id: string, file_type: DownloadFileType, queryParams?: PresenterQueryParams): string {
    let url: string = `http://localhost:8050/api/presenters/${id}/download/${file_type}`;

    if(queryParams) url += `?${new URLSearchParams(queryParams).toString()}`;

    return url;
}
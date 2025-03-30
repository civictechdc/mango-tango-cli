import { useState, useEffect, useRef, useMemo } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Input } from '@/components/ui/input.tsx';
import type { ReactElement, FC, ChangeEvent, MouseEvent, FormEvent, FocusEvent } from 'react';

export interface SearchBarProps {
    searchList: Array<string>;
    onSubmit: (value: string) => void;
    placeholder?: string;
}

export default function SearchBar({ searchList, onSubmit, placeholder }: SearchBarProps): ReactElement<FC> {
    const searchListRef = useRef<any>(null);
    const [showSearchList, setShowSearchList] = useState<boolean>(false);
    const [searchValue, setSearchValue] = useState<string>('');
    const handleChange = (e: ChangeEvent<HTMLInputElement>) => setSearchValue(e.target.value);
    const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        onSubmit(searchValue);
    };
    const handleClick = (e: MouseEvent<HTMLDivElement>) => setSearchValue(e.currentTarget.innerText);
    const searchSuggestionList = useMemo<Array<string>>(() => {
        if(searchValue.length === 0) return [];

        return searchList.filter((item: string): boolean => item.includes(searchValue));
    }, [searchValue]);
    const handleFocusIn = () => {
        if(searchSuggestionList.length > 1 && !showSearchList) setShowSearchList(true);
    };
    const handleFocusOut = (e: FocusEvent<HTMLInputElement>) => {
        if(showSearchList) setShowSearchList(false);
    };
    const searchListVirtualizer = useVirtualizer({
        count: searchSuggestionList.length,
        getScrollElement: () => searchListRef.current,
        estimateSize: () => 35
    });

    useEffect(() => {
        if(searchSuggestionList.length > 1 && !showSearchList) setShowSearchList(true);
        if(searchSuggestionList.length <= 1 && showSearchList) setShowSearchList(false);
    }, [searchSuggestionList]);

    useEffect(() => {
        if(!searchListRef.current) return;

        const divRef = (searchListRef.current as HTMLDivElement);

        if(!showSearchList && !divRef.classList.contains('invisible')) setTimeout(() => divRef.classList.add('invisible'), 140);
        if(showSearchList && divRef.classList.contains('invisible')) divRef.classList.remove('invisible');
    }, [showSearchList]);

    return (
        <form onSubmit={handleSubmit}>
            <Input
                type="text"
                className="w-80"
                value={searchValue}
                placeholder={placeholder != null && placeholder.length > 0 ? placeholder : 'Search Here...'}
                onChange={handleChange}
                onFocus={handleFocusIn}
                onBlur={handleFocusOut} />
            <div
                ref={searchListRef}
                data-state={showSearchList ? 'open' : 'closed'}
                className="absolute w-80 h-96 overflow-auto rounded-md bg-white text-zinc-950 border border-zinc-200 dark:bg-zinc-950 dark:text-zinc-50 dark:border-zinc-800 z-40 mt-2 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 slide-in-from-top-2 origin-(--radix-dropdown-menu-content-transform-origin)">
                <div
                    className="mt-2 relative size-full"
                    style={{height: `${searchListVirtualizer.getTotalSize()}px`}}>
                    {searchListVirtualizer.getVirtualItems().map((virtualItem: any) => (
                        <div
                            className="absolute top-0 left-0 w-full cursor-pointer p-2"
                            key={virtualItem.key}
                            onMouseDown={handleClick}
                            style={{
                                height: `${virtualItem.size}px`,
                                transform: `translateY(${virtualItem.start}px)`,
                            }}
                        >
                            {searchSuggestionList[virtualItem.index]}
                        </div>
                    ))}
                </div>
            </div>
        </form>
    );
}
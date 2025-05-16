
declare global {
    interface Window {
        PROJECT_NAME: string;
    }
}

declare module '*.css' {
    const content: any;
    export default content;
}

export {};
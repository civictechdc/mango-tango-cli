export default function calculateRankings(arr: Array<number>){
        const Sorted = [...(arr)].sort(( a,  b) => b - a);
        return (arr).map((x) => Sorted.indexOf(x) + 1);
    };


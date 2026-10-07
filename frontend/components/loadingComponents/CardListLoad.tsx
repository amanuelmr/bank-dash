import { CardListSkeleton } from "./CardListSkeleton"

const CardListLoad = () => {
  return (
    <div className="w-full">
        <CardListSkeleton />
        <CardListSkeleton />
        <CardListSkeleton />
        <CardListSkeleton />
    </div>
  )
}

export default CardListLoad

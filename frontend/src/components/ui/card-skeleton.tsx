import { Card, CardContent, CardHeader } from "./card";
import { Skeleton } from "./skeleton";

export function CardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-center">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="ml-auto w-4 h-4 rounded-full" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="sm:flex sm:justify-between sm:items-center">
          <Skeleton className="h-8 w-24" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-16" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function CardSkeletonLarge() {
  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-center">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="ml-auto w-4 h-4 rounded-full" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="sm:flex sm:justify-between sm:items-center">
          <Skeleton className="h-8 w-24" />
        </div>
        <div className="flex items-center gap-2 mt-2 mb-10">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-4 w-4 rounded-full" />
        </div>
        <Skeleton className="h-32 w-full rounded-md" />
      </CardContent>
    </Card>
  );
}

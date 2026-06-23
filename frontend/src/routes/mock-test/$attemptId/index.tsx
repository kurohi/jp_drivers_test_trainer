import { createRoute, useNavigate } from "@tanstack/react-router";
import { Skeleton } from "@/components/ui/skeleton";
import { MockTestRunner } from "@/components/features/mock-test/MockTestRunner";
import { useMockTestStore } from "@/store/mock-test";
import { Route as rootRoute } from "../../__root";

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/mock-test/$attemptId",
  component: MockTestRunnerPage,
});

function MockTestRunnerPage() {
  const navigate = useNavigate();
  const { attemptId } = useMockTestStore();
  const { attemptId: paramAttemptId } = Route.useParams();

  if (!attemptId || String(attemptId) !== paramAttemptId) {
    navigate({ to: "/mock-test" });
    return (
      <div className="container mx-auto py-8">
        <Skeleton className="h-10 w-64 mb-4" />
        <Skeleton className="h-64 rounded-lg" />
      </div>
    );
  }

  return <MockTestRunner attemptId={attemptId} paramAttemptId={paramAttemptId} />;
}
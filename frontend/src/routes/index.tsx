import { createRoute } from "@tanstack/react-router"
import { Route as rootRoute } from "./__root"

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: IndexPage,
})

function IndexPage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold">JP Drivers Test Trainer</h1>
      <p className="mt-2 text-muted-foreground">
        Your Japanese driver&apos;s license test preparation tool.
      </p>
    </div>
  )
}
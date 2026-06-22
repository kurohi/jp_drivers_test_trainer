import { createRootRoute, createRoute, createRouter, Outlet } from "@tanstack/react-router";

export const rootRoute = createRootRoute({
  component: () => (
    <div className="min-h-screen bg-background text-foreground">
      <Outlet />
    </div>
  ),
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: () => (
    <main className="container mx-auto py-8">
      <h1 className="text-3xl font-bold">JP Drivers Test Trainer</h1>
      <p className="mt-2 text-muted-foreground">
        Your Japanese driver&apos;s license test preparation tool.
      </p>
    </main>
  ),
});

const routeTree = rootRoute.addChildren([indexRoute]);

export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
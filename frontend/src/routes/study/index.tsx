import { createRoute } from "@tanstack/react-router"
import { useTranslation } from "react-i18next"
import { Route as rootRoute } from "../__root"

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/study",
  component: StudyPage,
})

function StudyPage() {
  const { t } = useTranslation()

  return (
    <div className="container mx-auto py-8">
      <h1 data-testid="page-title" className="text-3xl font-bold">
        {t("pageTitle.study")}
      </h1>
      <p className="mt-2 text-muted-foreground">Coming soon</p>
    </div>
  )
}
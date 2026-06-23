import { createRoute, Link } from "@tanstack/react-router"
import { useTranslation } from "react-i18next"
import { useQuery } from "@tanstack/react-query"
import { Route as rootRoute } from "../__root"
import { api } from "@/lib/api"
import { useUIStore } from "@/store/ui"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/skill-test",
  component: SkillTestPage,
})

function SkillTestPage() {
  const { t } = useTranslation()
  const language = useUIStore((s) => s.language)

  const { data: modules, isLoading, isError } = useQuery({
    queryKey: ["skill-modules"],
    queryFn: () => api.skill.list(),
  })

  return (
    <div className="container mx-auto py-8">
      <h1 data-testid="page-title" className="text-3xl font-bold">
        {t("pageTitle.skillTest")}
      </h1>
      <p className="mt-2 text-muted-foreground">{t("skillTest.subtitle")}</p>

      {isLoading && (
        <div
          data-testid="skill-grid-loading"
          className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
        >
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-lg" />
          ))}
        </div>
      )}

      {isError && (
        <p className="mt-6 text-destructive" data-testid="skill-grid-error">
          {t("skillTest.noModules")}
        </p>
      )}

      {modules && modules.length > 0 && (
        <div
          data-testid="skill-grid"
          className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
        >
          {modules.map((mod) => (
            <Link
              key={mod.id}
              to="/skill-test/$slug"
              params={{ slug: mod.slug }}
              data-testid={`skill-card-${mod.slug}`}
              className="block text-left transition-transform hover:scale-[1.02] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-lg"
            >
              <Card className="h-full transition-shadow hover:shadow-md">
                {/* SVG thumbnail */}
                <div className="flex h-32 items-center justify-center overflow-hidden rounded-t-lg bg-muted/30">
                  <img
                    src={`/assets/skill/${mod.slug}-diagram.svg`}
                    alt={language === "en" ? mod.name_en : mod.name_pt}
                    className="h-full w-full object-contain"
                    loading="lazy"
                  />
                </div>

                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base leading-tight">
                      {language === "en" ? mod.name_en : mod.name_pt}
                    </CardTitle>
                    <Badge variant="secondary" className="shrink-0">
                      {mod.sort_order}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent>
                  <p className="text-xs text-muted-foreground">
                    {language === "en" ? mod.name_pt : mod.name_en}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

      {modules && modules.length === 0 && !isLoading && (
        <p
          className="mt-6 text-muted-foreground"
          data-testid="skill-grid-empty"
        >
          {t("skillTest.noModules")}
        </p>
      )}
    </div>
  )
}
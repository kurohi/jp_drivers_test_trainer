import { createRoute, Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { Route as rootRoute } from "../__root";
import { api } from "@/lib/api";
import { useUIStore } from "@/store/ui";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/study",
  component: StudyPage,
});

function StudyPage() {
  const { t } = useTranslation();
  const language = useUIStore((s) => s.language);

  const { data: themes, isLoading, isError } = useQuery({
    queryKey: ["themes"],
    queryFn: () => api.themes.list(),
  });

  return (
    <div className="container mx-auto py-8">
      <h1 data-testid="page-title" className="text-3xl font-bold">
        {t("pageTitle.study")}
      </h1>

      <div className="mt-2 mb-6">
        <h2 className="text-lg font-semibold text-foreground">
          {t("study.themeGridTitle")}
        </h2>
        <p className="text-sm text-muted-foreground">
          {t("study.themeGridSubtitle")}
        </p>
      </div>

      {isLoading && (
        <div
          data-testid="theme-grid-loading"
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
        >
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-lg" />
          ))}
        </div>
      )}

      {isError && (
        <p className="text-destructive" data-testid="theme-grid-error">
          {t("study.noThemes")}
        </p>
      )}

      {themes && themes.length > 0 && (
        <div
          data-testid="theme-grid"
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
        >
          {themes.map((theme) => (
            <Link
              key={theme.id}
              to="/study/$themeSlug"
              params={{ themeSlug: theme.slug }}
              data-testid={`theme-card-${theme.slug}`}
              className="block text-left transition-transform hover:scale-[1.02] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-lg"
            >
              <Card className="h-full transition-shadow hover:shadow-md">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base leading-tight">
                      {language === "en" ? theme.name_en : theme.name_pt}
                    </CardTitle>
                    <Badge variant="secondary" className="shrink-0">
                      {theme.sort_order}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground">
                    {language === "en" ? theme.name_pt : theme.name_en}
                  </p>
                  <p
                    className="mt-2 text-sm font-medium text-foreground"
                    data-testid={`theme-count-${theme.slug}`}
                  >
                    {t("study.questionsCount", { count: theme.question_count })}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

      {themes && themes.length === 0 && !isLoading && (
        <p className="text-muted-foreground" data-testid="theme-grid-empty">
          {t("study.noThemes")}
        </p>
      )}
    </div>
  );
}
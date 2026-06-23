import { createRoute } from "@tanstack/react-router"
import { useTranslation } from "react-i18next"
import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Route as rootRoute } from "../__root"
import { api } from "@/lib/api"
import { useUIStore } from "@/store/ui"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import type { StudyPlanOut } from "@/types"

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/plan",
  component: PlanPage,
})

function PlanPage() {
  const { t } = useTranslation()
  const language = useUIStore((s) => s.language)

  const [availableDays, setAvailableDays] = useState(7)
  const [hoursPerDay, setHoursPerDay] = useState(1.5)
  const [currentPlan, setCurrentPlan] = useState<StudyPlanOut | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [showHistory, setShowHistory] = useState(false)

  const { data: themes } = useQuery({
    queryKey: ["themes"],
    queryFn: () => api.themes.list(),
  })

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ["study-plans-history"],
    queryFn: () => api.studyPlans.history(10),
    enabled: showHistory,
  })

  const themeMap = new Map(
    (themes ?? []).map((t) => [t.id, t]),
  )

  const handleGenerate = async () => {
    setIsGenerating(true)
    try {
      const plan = await api.studyPlans.generate({
        available_days: availableDays,
        hours_per_day: hoursPerDay,
      })
      setCurrentPlan(plan)
      setShowHistory(false)
    } catch {
      // error handled by parent
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="container mx-auto py-8">
      <h1 data-testid="page-title" className="text-3xl font-bold">
        {t("pageTitle.plan")}
      </h1>
      <p className="mt-2 text-muted-foreground">{t("plan.subtitle")}</p>

      {/* Generate form */}
      <Card className="mt-6" data-testid="plan-form">
        <CardHeader>
          <CardTitle className="text-lg">
            {t("plan.generate")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="available-days"
                className="text-xs font-medium text-muted-foreground"
              >
                {t("plan.availableDays")}
              </label>
              <input
                id="available-days"
                type="number"
                min={1}
                max={30}
                value={availableDays}
                onChange={(e) => setAvailableDays(Number(e.target.value))}
                data-testid="plan-available-days"
                className="w-24 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="hours-per-day"
                className="text-xs font-medium text-muted-foreground"
              >
                {t("plan.hoursPerDay")}
              </label>
              <input
                id="hours-per-day"
                type="number"
                min={0.5}
                max={8}
                step={0.5}
                value={hoursPerDay}
                onChange={(e) => setHoursPerDay(Number(e.target.value))}
                data-testid="plan-hours-per-day"
                className="w-24 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
            </div>

            <Button
              onClick={handleGenerate}
              disabled={isGenerating}
              data-testid="plan-generate"
            >
              {isGenerating
                ? t("plan.generating")
                : t("plan.generate")}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Current plan timeline */}
      {currentPlan && !showHistory && (
        <div className="mt-8" data-testid="plan-timeline">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-semibold">
                {t(`plan.planSource.${currentPlan.source}`)}
              </h2>
              <Badge variant="secondary">
                {new Date(currentPlan.created_at).toLocaleDateString()}
              </Badge>
            </div>
            <Button
              variant="link"
              size="sm"
              onClick={() => setShowHistory(true)}
              data-testid="plan-view-history"
            >
              {t("plan.viewHistory")}
            </Button>
          </div>

          <div className="space-y-3">
            {currentPlan.days.map((day, idx) => (
              <Card key={idx} data-testid={`plan-day-${idx}`}>
                <CardContent className="flex items-start gap-4 pt-6">
                  {/* Day number badge */}
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
                    {idx + 1}
                  </div>

                  <div className="flex-1 space-y-2">
                    {/* Date */}
                    <p className="text-xs font-medium text-muted-foreground">
                      {t("plan.day", { n: idx + 1 })} —{" "}
                      {new Date(day.date).toLocaleDateString(
                        language === "en" ? "en-US" : "pt-BR",
                        {
                          weekday: "short",
                          month: "short",
                          day: "numeric",
                        },
                      )}
                    </p>

                    {/* Theme badges */}
                    <div className="flex flex-wrap gap-1.5">
                      {day.theme_ids.map((tid) => {
                        const theme = themeMap.get(tid)
                        if (!theme) return null
                        return (
                          <Badge
                            key={tid}
                            variant="outline"
                            className="text-xs"
                          >
                            {language === "en"
                              ? theme.name_en
                              : theme.name_pt}
                          </Badge>
                        )
                      })}
                    </div>

                    {/* Question count */}
                    <p className="text-sm text-muted-foreground">
                      {t("plan.questions", { count: day.question_count })}
                    </p>

                    {/* Focus note */}
                    <p className="text-sm font-medium">
                      {t("plan.focusNote")}:{" "}
                      <span className="font-normal text-muted-foreground">
                        {language === "en"
                          ? day.focus_note_en
                          : day.focus_note_pt}
                      </span>
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* History */}
      {showHistory && (
        <div className="mt-8" data-testid="plan-history">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              {t("plan.historyTitle")}
            </h2>
            <Button
              variant="link"
              size="sm"
              onClick={() => setShowHistory(false)}
              data-testid="plan-back-to-plan"
            >
              {t("plan.backToPlan")}
            </Button>
          </div>

          {historyLoading && (
            <div className="space-y-3">
              {Array.from({ length: 2 }).map((_, i) => (
                <Skeleton key={i} className="h-24 rounded-lg" />
              ))}
            </div>
          )}

          {history && history.length === 0 && (
            <Card data-testid="plan-history-empty">
              <CardContent className="py-8 text-center">
                <p className="text-muted-foreground">
                  {t("plan.noHistory")}
                </p>
              </CardContent>
            </Card>
          )}

          {history && history.length > 0 && (
            <div className="space-y-3">
              {history.map((plan) => (
                <button
                  key={plan.id}
                  onClick={() => {
                    setCurrentPlan(plan)
                    setShowHistory(false)
                  }}
                  className="w-full text-left"
                  data-testid={`plan-history-item-${plan.id}`}
                >
                  <Card className="transition-shadow hover:shadow-md">
                    <CardContent className="flex items-center gap-4 pt-6">
                      <Badge variant="secondary">
                        {t(`plan.planSource.${plan.source}`)}
                      </Badge>
                      <span className="text-sm text-muted-foreground">
                        {new Date(plan.created_at).toLocaleDateString()}
                      </span>
                      <span className="text-sm text-muted-foreground">
                        {plan.days.length} days
                      </span>
                    </CardContent>
                  </Card>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Empty state: no plan generated and no history shown */}
      {!currentPlan && !showHistory && (
        <Card className="mt-8" data-testid="plan-empty-state">
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">
              {t("plan.noHistory")}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

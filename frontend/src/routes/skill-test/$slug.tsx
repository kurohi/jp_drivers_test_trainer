import { createRoute, Link } from "@tanstack/react-router"
import { useTranslation } from "react-i18next"
import { useQuery } from "@tanstack/react-query"
import { useState, useMemo } from "react"
import { Route as rootRoute } from "../__root"
import { api } from "@/lib/api"
import { useUIStore } from "@/store/ui"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { TrajectoryPlayer } from "@/components/trajectory-player"

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/skill-test/$slug",
  component: SkillTestDetailPage,
})

// ─── Types for parsed JSON fields ────────────────────────────────────────────

interface ChecklistItem {
  step: number
  text: { en: string; pt: string }
  pass_criteria: { en: string; pt: string }
}

interface CommonMistakes {
  en: string[]
  pt: string[]
}

interface WrongTrajectory {
  path: { x: number; y: number }[]
  failure_reason_en?: string
  failure_reason_pt?: string
}

// ─── Page Component ──────────────────────────────────────────────────────────

function SkillTestDetailPage() {
  const { t } = useTranslation()
  const language = useUIStore((s) => s.language)
  const { slug } = Route.useParams()

  const { data: module, isLoading, isError } = useQuery({
    queryKey: ["skill-module", slug],
    queryFn: () => api.skill.getBySlug(slug),
  })

  // Parse JSON fields
  const checklist = useMemo<ChecklistItem[] | null>(() => {
    if (!module?.checklist_json) return null
    try {
      return JSON.parse(module.checklist_json) as ChecklistItem[]
    } catch {
      return null
    }
  }, [module?.checklist_json])

  const commonMistakes = useMemo<CommonMistakes | null>(() => {
    if (!module?.common_mistakes_json) return null
    try {
      return JSON.parse(module.common_mistakes_json) as CommonMistakes
    } catch {
      return null
    }
  }, [module?.common_mistakes_json])

  const wrongTrajectory = useMemo<WrongTrajectory | null>(() => {
    if (!module?.wrong_trajectory_json) return null
    try {
      return JSON.parse(module.wrong_trajectory_json) as WrongTrajectory
    } catch {
      return null
    }
  }, [module?.wrong_trajectory_json])

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <Skeleton className="h-10 w-48 mb-4" />
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Skeleton className="h-96 rounded-lg" />
          <Skeleton className="h-96 rounded-lg" />
        </div>
      </div>
    )
  }

  if (isError || !module) {
    return (
      <div className="container mx-auto py-8">
        <p className="text-muted-foreground" data-testid="module-not-found">
          {t("skillTest.moduleNotFound")}
        </p>
        <Button asChild variant="outline" className="mt-4">
          <Link to="/skill-test">{t("skillTest.backToModules")}</Link>
        </Button>
      </div>
    )
  }

  const name = language === "en" ? module.name_en : module.name_pt
  const nameAlt = language === "en" ? module.name_pt : module.name_en
  const overview = language === "en" ? module.overview_en : module.overview_pt
  const proTip = language === "en" ? module.pro_tip_en : module.pro_tip_pt
  const failureReason = language === "en"
    ? wrongTrajectory?.failure_reason_en
    : wrongTrajectory?.failure_reason_pt

  return (
    <div className="container mx-auto py-8">
      {/* Header */}
      <div className="mb-6">
        <Button asChild variant="ghost" size="sm" className="mb-2">
          <Link to="/skill-test" data-testid="back-to-modules">
            ← {t("skillTest.backToModules")}
          </Link>
        </Button>
        <h1 data-testid="page-title" className="text-3xl font-bold">
          {name}
        </h1>
        <p className="text-sm text-muted-foreground">{nameAlt}</p>
      </div>

      {/* Overview */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <p className="text-sm leading-relaxed text-foreground">
            {overview}
          </p>
        </CardContent>
      </Card>

      {/* Side-by-side layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Left: SVG diagram + trajectory buttons */}
        <div>
          <Card data-testid="skill-diagram-card">
            <CardHeader>
              <CardTitle className="text-lg">
                {t("skillTest.overview")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* SVG diagram */}
              <div className="flex items-center justify-center rounded-lg bg-muted/30 p-4">
                <img
                  src={`/assets/skill/${module.slug}-diagram.svg`}
                  alt={name}
                  className="w-full max-w-md"
                  data-testid="skill-diagram-svg"
                />
              </div>

              {/* Trajectory buttons */}
              <div className="mt-4 flex flex-wrap gap-3">
                <Button
                  variant="default"
                  size="sm"
                  data-testid="play-correct"
                  className="bg-green-600 hover:bg-green-600/90"
                >
                  {t("skillTest.playCorrect")}
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  data-testid="play-wrong"
                  className="bg-red-600 hover:bg-red-600/90"
                >
                  {t("skillTest.playWrong")}
                </Button>
              </div>

              {/* Trajectory player — correct */}
              <div className="mt-4">
                <TrajectoryPlayer
                  trajectoryJson={module.correct_trajectory_json}
                  color="#22c55e"
                />
              </div>

              {/* Trajectory player — wrong */}
              <div className="mt-4">
                <TrajectoryPlayer
                  trajectoryJson={module.wrong_trajectory_json}
                  color="#ef4444"
                  isWrong
                  failureReason={failureReason}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right: checklist + common mistakes + pro tip */}
        <div className="space-y-6">
          {/* Checklist (click-advance) */}
          {checklist && (
            <Card data-testid="skill-checklist-card">
              <CardHeader>
                <CardTitle className="text-lg">
                  {t("skillTest.checklist")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Checklist
                  items={checklist}
                  language={language}
                  t={t}
                />
              </CardContent>
            </Card>
          )}

          {/* Common mistakes */}
          {commonMistakes && (
            <Card data-testid="skill-mistakes-card">
              <CardHeader>
                <CardTitle className="text-lg">
                  {t("skillTest.commonMistakes")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {(language === "en" ? commonMistakes.en : commonMistakes.pt).map(
                    (mistake, idx) => (
                      <li
                        key={idx}
                        className="flex items-start gap-2 text-sm"
                      >
                        <span className="mt-0.5 text-destructive">✗</span>
                        <span className="text-foreground">{mistake}</span>
                      </li>
                    ),
                  )}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Pro tip */}
          <Card data-testid="skill-protip-card">
            <CardHeader>
              <CardTitle className="text-lg">
                {t("skillTest.proTip")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border border-primary/30 bg-primary/5 p-3">
                <p className="text-sm italic text-foreground">{proTip}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

// ─── Checklist (click-advance, no auto-advance) ──────────────────────────────

interface ChecklistProps {
  items: ChecklistItem[]
  language: "en" | "pt"
  t: (key: string, opts?: Record<string, unknown>) => string
}

function Checklist({ items, language, t }: ChecklistProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const isComplete = currentStep >= items.length

  const handleNext = () => {
    if (currentStep < items.length) {
      setCurrentStep((s) => s + 1)
    }
  }

  if (isComplete) {
    return (
      <div
        data-testid="checklist-complete"
        className="flex flex-col items-center gap-3 py-4"
      >
        <Badge variant="default" className="bg-green-600">
          ✓ {t("skillTest.checklistComplete")}
        </Badge>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setCurrentStep(0)}
          data-testid="checklist-reset"
        >
          {t("common.buttons.reset")}
        </Button>
      </div>
    )
  }

  const item = items[currentStep]
  const text = language === "en" ? item.text.en : item.text.pt
  const passCriteria = language === "en"
    ? item.pass_criteria.en
    : item.pass_criteria.pt

  return (
    <div data-testid="checklist-step">
      {/* Progress indicator */}
      <div className="mb-4 flex items-center gap-2">
        {items.map((_, idx) => (
          <div
            key={idx}
            className={`h-2 flex-1 rounded-full ${
              idx <= currentStep ? "bg-primary" : "bg-muted"
            }`}
          />
        ))}
      </div>

      {/* Step label */}
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {t("skillTest.step", { current: currentStep + 1, total: items.length })}
      </p>

      {/* Step text */}
      <p className="text-sm font-medium leading-relaxed text-foreground">
        {text}
      </p>

      {/* Pass criteria */}
      <div className="mt-3 rounded-md border bg-muted/30 p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {t("skillTest.passCriteria")}
        </p>
        <p className="mt-1 text-sm text-foreground">{passCriteria}</p>
      </div>

      {/* Next button (click-advance only, no auto-advance) */}
      <Button
        variant="default"
        size="sm"
        onClick={handleNext}
        className="mt-4"
        data-testid="checklist-next"
      >
        {t("skillTest.nextStep")}
      </Button>
    </div>
  )
}
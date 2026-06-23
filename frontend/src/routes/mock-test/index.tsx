import { createRoute, useNavigate } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { useState } from "react";
import { Route as rootRoute } from "../__root";
import { api } from "@/lib/api";
import { useUIStore } from "@/store/ui";
import { useMockTestStore } from "@/store/mock-test";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { Difficulty } from "@/types";

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/mock-test",
  component: MockTestStartPage,
});

const DIFFICULTY_STOPS: { value: Difficulty; key: string }[] = [
  { value: 0.0, key: "beginner" },
  { value: 0.25, key: "easy" },
  { value: 0.5, key: "standard" },
  { value: 0.75, key: "hard" },
  { value: 1.0, key: "expert" },
];

function MockTestStartPage() {
  const { t } = useTranslation();
  const language = useUIStore((s) => s.language);
  const navigate = useNavigate();
  const setAttempt = useMockTestStore((s) => s.setAttempt);

  const [difficulty, setDifficulty] = useState<Difficulty>(0.5);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const difficultyIndex = DIFFICULTY_STOPS.findIndex((d) => d.value === difficulty);
  const currentDifficultyKey = DIFFICULTY_STOPS[difficultyIndex]?.key ?? "standard";

  async function handleStart() {
    setStarting(true);
    setError(null);
    try {
      const result = await api.mockTests.start({
        language,
        theme_ids: null,
        question_count: 50,
        tricky_ratio: difficulty,
        time_limit_seconds: 1800,
        seed: null,
      });
      setAttempt({
        attemptId: result.attempt_id,
        questions: result.questions,
        timeLimitSeconds: result.time_limit_seconds,
      });
      navigate({
        to: "/mock-test/$attemptId",
        params: { attemptId: String(result.attempt_id) },
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start test");
      setStarting(false);
    }
  }

  return (
    <div className="container mx-auto py-8">
      <h1 data-testid="page-title" className="text-3xl font-bold">
        {t("pageTitle.mockTest")}
      </h1>
      <p className="mt-2 text-muted-foreground">{t("mockTest.startSubtitle")}</p>

      <Card className="mt-6 max-w-2xl" data-testid="mock-test-start-card">
        <CardHeader>
          <CardTitle>{t("mockTest.startTitle")}</CardTitle>
          <CardDescription>
            <Badge variant="secondary" className="mr-2" data-testid="exam-format-badge">
              {t("mockTest.examFormat")}
            </Badge>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Locked format notice */}
          <div className="rounded-md border bg-muted/30 p-4 space-y-1" data-testid="locked-format-notice">
            <p className="text-sm font-medium">{t("mockTest.questionCount")}</p>
            <p className="text-sm font-medium">{t("mockTest.timeLimit")}</p>
            <p className="text-sm font-medium">{t("mockTest.passThreshold")}</p>
          </div>

          {/* Difficulty slider */}
          <div className="space-y-3" data-testid="difficulty-section">
            <label className="text-sm font-semibold" htmlFor="difficulty-slider">
              {t("mockTest.difficultyLabel")}
            </label>
            <div className="flex items-center gap-2">
              <input
                id="difficulty-slider"
                type="range"
                min={0}
                max={4}
                step={1}
                value={difficultyIndex}
                onChange={(e) => {
                  const idx = Number(e.target.value);
                  setDifficulty(DIFFICULTY_STOPS[idx].value);
                }}
                className="flex-1 h-2 cursor-pointer appearance-none rounded-full bg-secondary accent-primary"
                data-testid="difficulty-slider"
              />
              <Badge variant="default" className="min-w-24 justify-center" data-testid="difficulty-label">
                {t(`common.difficulty.${currentDifficultyKey}`)}
              </Badge>
            </div>
            <div className="flex justify-between text-xs text-muted-foreground">
              {DIFFICULTY_STOPS.map((d) => (
                <span key={d.value}>{t(`common.difficulty.${d.key}`)}</span>
              ))}
            </div>
          </div>

          {/* Error */}
          {error && (
            <p className="text-sm text-destructive" data-testid="start-error">
              {error}
            </p>
          )}

          {/* Start button */}
          <Button
            size="lg"
            className="w-full"
            onClick={handleStart}
            disabled={starting}
            data-testid="start-mock-test-btn"
          >
            {starting ? (
              <>
                <Skeleton className="h-4 w-24" />
                <span className="ml-2">{t("mockTest.starting")}</span>
              </>
            ) : (
              t("mockTest.startButton")
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
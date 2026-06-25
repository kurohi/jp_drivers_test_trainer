import { createRoute, useNavigate, Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { useState } from "react";
import { Route as rootRoute } from "../../__root";
import { useUIStore } from "@/store/ui";
import { useMockTestStore } from "@/store/mock-test";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { AttemptAnswerOut } from "@/types";

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/mock-test/$attemptId/result",
  component: MockTestResultPage,
});

function MockTestResultPage() {
  const { t } = useTranslation();
  const language = useUIStore((s) => s.language);
  const navigate = useNavigate();
  const { result, reset } = useMockTestStore();

  if (!result) {
    return (
      <div className="container mx-auto py-8">
        <p className="text-muted-foreground" data-testid="no-result">
          {t("mockTest.noResult")}
        </p>
        <Button asChild variant="outline" className="mt-4">
          <Link to="/mock-test">{t("mockTest.backToStart")}</Link>
        </Button>
      </div>
    );
  }

  const passed = result.passed;
  const score = result.score;
  const maxScore = result.max_score;
  const percentage = Math.round((score / maxScore) * 100);

  return (
    <div className="container mx-auto py-8 max-w-3xl">
      <h1 data-testid="page-title" className="text-3xl font-bold">
        {t("mockTest.resultTitle")}
      </h1>

      {/* PASS/FAIL banner */}
      <Card
        className={cn(
          "mt-6 border-2",
          passed ? "border-green-500/50 bg-green-500/5" : "border-destructive/50 bg-destructive/5",
        )}
        data-testid="result-banner"
      >
        <CardContent className="pt-6 text-center">
          <div
            className={cn(
              "text-6xl font-bold tracking-tight",
              passed ? "text-green-600 dark:text-green-400" : "text-destructive",
            )}
            data-testid="pass-fail-label"
          >
            {passed ? t("mockTest.passed") : t("mockTest.failed")}
          </div>
          <p className="mt-4 text-lg font-medium" data-testid="score-display">
            {t("mockTest.scoreDisplay", { score, max: maxScore })}
          </p>
          <p className="mt-1 text-sm text-muted-foreground" data-testid="score-percentage">
            {percentage}%
          </p>
          <p
            className={cn(
              "mt-3 text-sm",
              passed ? "text-green-600 dark:text-green-400" : "text-destructive",
            )}
            data-testid="pass-fail-message"
          >
            {passed ? t("mockTest.passMessage") : t("mockTest.failMessage")}
          </p>
        </CardContent>
      </Card>

      {/* Action buttons */}
      <div className="mt-6 flex gap-4" data-testid="result-actions">
        <Button
          variant="outline"
          className="flex-1"
          onClick={() => {
            reset();
            navigate({ to: "/mock-test" });
          }}
          data-testid="take-another-btn"
        >
          {t("mockTest.takeAnother")}
        </Button>
        <Button
          asChild
          className="flex-1"
          data-testid="generate-plan-btn"
        >
          <Link to="/plan">{t("mockTest.generatePlan")}</Link>
        </Button>
      </div>

      {/* Question review */}
      <div className="mt-8">
        <h2 className="text-xl font-bold" data-testid="review-title">
          {t("mockTest.reviewTitle")}
        </h2>
        <p className="text-sm text-muted-foreground mb-4">
          {t("mockTest.reviewSubtitle")}
        </p>

        <div className="space-y-3" data-testid="review-list">
          {result.answers.map((answer, idx) => (
            <ReviewItem
              key={answer.question_id}
              answer={answer}
              index={idx}
              language={language}
              t={t}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

interface ReviewItemProps {
  answer: AttemptAnswerOut;
  index: number;
  language: "en" | "pt";
  t: (key: string, opts?: Record<string, unknown>) => string;
}

function ReviewItem({ answer, index, language, t }: ReviewItemProps) {
  const [expanded, setExpanded] = useState(false);

  const prompt =
    language === "en" ? answer.prompt_en || "" : answer.prompt_pt || "";
  const userAnswerLabel =
    answer.user_answer === "true"
      ? t("common.buttons.true")
      : t("common.buttons.false");
  const correctAnswerLabel =
    answer.correct_answer === "true"
      ? t("common.buttons.true")
      : t("common.buttons.false");
  const explanation =
    language === "en" ? answer.explanation_en : answer.explanation_pt;

  return (
    <Card data-testid={`review-item-${index}`} className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          <span
            className={cn(
              "mt-0.5 h-3 w-3 shrink-0 rounded-full",
              answer.is_correct ? "bg-green-500" : "bg-destructive",
            )}
            data-testid={`review-chip-${index}`}
          />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-muted-foreground">
                {index + 1}.
              </span>
              <Badge variant={answer.is_correct ? "default" : "destructive"} className="text-xs">
                {answer.is_correct ? t("study.correct") : t("study.incorrect")}
              </Badge>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {/* Question image */}
        {answer.image_url && (
          <div className="mb-3 flex justify-center" data-testid={`review-image-${index}`}>
            <img
              src={answer.image_url}
              alt={t("mockTest.questionImageAlt")}
              className="max-h-48 w-auto rounded-lg border object-contain"
            />
          </div>
        )}
        {/* Question prompt */}
        {prompt && (
          <p className="mb-3 text-sm font-medium leading-relaxed" data-testid={`review-prompt-${index}`}>
            {prompt}
          </p>
        )}
        {/* Answer summary */}
        <div className="space-y-1 text-sm mb-3">
          <p className="text-muted-foreground">
            <span className="font-medium">{t("mockTest.yourAnswerLabel")}:</span>{" "}
            <span className={answer.is_correct ? "text-green-600 dark:text-green-400" : "text-destructive"}>
              {userAnswerLabel}
            </span>
          </p>
          <p className="text-muted-foreground">
            <span className="font-medium">{t("mockTest.correctAnswerLabel")}:</span>{" "}
            <span className="font-medium text-foreground">{correctAnswerLabel}</span>
          </p>
        </div>

        {/* Expandable explanation */}
        <button
          onClick={() => setExpanded((prev) => !prev)}
          className="flex items-center gap-1 text-sm font-medium text-primary hover:underline"
          data-testid={`review-why-${index}`}
          aria-expanded={expanded}
        >
          {t("mockTest.whyLabel")}
          <span className="text-xs">{expanded ? "▲" : "▼"}</span>
        </button>

        {expanded && (
          <div
            className="mt-3 rounded-md border bg-muted/30 p-4"
            data-testid={`review-explanation-${index}`}
          >
            <p className="text-sm leading-relaxed text-foreground">{explanation}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
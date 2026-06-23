import { createRoute, Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { useState, useCallback } from "react";
import { Route as rootRoute } from "../../__root";
import { api } from "@/lib/api";
import { useUIStore } from "@/store/ui";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { QuestionListItem, QuestionDetail } from "@/types";

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/study/$themeSlug",
  component: ThemeStudyPage,
});

const PAGE_SIZE = 10;

type UserChoice = "true" | "false" | null;

function ThemeStudyPage() {
  const { t } = useTranslation();
  const language = useUIStore((s) => s.language);
  const { themeSlug } = Route.useParams();

  // ─── Theme lookup ──────────────────────────────────────────────────────
  const { data: theme, isLoading: themeLoading } = useQuery({
    queryKey: ["theme", themeSlug],
    queryFn: () => api.themes.getBySlug(themeSlug),
  });

  // ─── Paginated question list ──────────────────────────────────────────
  const [page, setPage] = useState(1);

  const { data: questionData, isLoading: questionsLoading } = useQuery({
    queryKey: ["questions", theme?.id, page],
    queryFn: () => api.questions.listByTheme(theme!.id, page, PAGE_SIZE),
    enabled: !!theme,
  });

  if (themeLoading) {
    return (
      <div className="container mx-auto py-8">
        <Skeleton className="h-10 w-64 mb-4" />
        <Skeleton className="h-64 rounded-lg" />
      </div>
    );
  }

  if (!theme) {
    return (
      <div className="container mx-auto py-8">
        <p className="text-muted-foreground" data-testid="theme-not-found">
          {t("study.themeNotFound")}
        </p>
        <Button asChild variant="outline" className="mt-4">
          <Link to="/study">{t("study.backToThemes")}</Link>
        </Button>
      </div>
    );
  }

  const themeName = language === "en" ? theme.name_en : theme.name_pt;
  const themeNameAlt = language === "en" ? theme.name_pt : theme.name_en;

  return (
    <div className="container mx-auto py-8">
      {/* Header */}
      <div className="mb-6">
        <Button asChild variant="ghost" size="sm" className="mb-2">
          <Link to="/study" data-testid="back-to-themes">
            ← {t("study.backToThemes")}
          </Link>
        </Button>
        <h1
          data-testid="page-title"
          className="text-3xl font-bold"
        >
          {themeName}
        </h1>
        <p className="text-sm text-muted-foreground">{themeNameAlt}</p>
      </div>

      {/* Question list */}
      {questionsLoading ? (
        <div data-testid="question-list-loading" className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-lg" />
          ))}
        </div>
      ) : questionData && questionData.items.length > 0 ? (
        <>
          <div className="space-y-4" data-testid="question-list">
            {questionData.items.map((question, idx) => (
              <QuestionCard
                key={question.id}
                question={question}
                index={idx}
                language={language}
                t={t}
              />
            ))}
          </div>

          {/* Pagination */}
          {questionData.totalPages > 1 && (
            <div className="mt-6 flex items-center justify-center gap-4">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                data-testid="pagination-prev"
              >
                {t("common.buttons.previous")}
              </Button>
              <span className="text-sm text-muted-foreground" data-testid="pagination-info">
                {t("study.page", {
                  current: page,
                  total: questionData.totalPages,
                })}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= questionData.totalPages}
                onClick={() => setPage((p) => p + 1)}
                data-testid="pagination-next"
              >
                {t("common.buttons.next")}
              </Button>
            </div>
          )}
        </>
      ) : (
        <p className="text-muted-foreground" data-testid="question-list-empty">
          {t("study.noQuestions")}
        </p>
      )}
    </div>
  );
}

// ─── Question Card ──────────────────────────────────────────────────────────

interface QuestionCardProps {
  question: QuestionListItem;
  index: number;
  language: "en" | "pt";
  t: (key: string, opts?: Record<string, unknown>) => string;
}

function QuestionCard({ question, index, language, t }: QuestionCardProps) {
  const [userChoice, setUserChoice] = useState<UserChoice>(null);
  const [showExplanation, setShowExplanation] = useState(false);

  // Detail fetch — only triggered when user clicks "Show explanation"
  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ["question-detail", question.id],
    queryFn: () => api.questions.getById(question.id),
    enabled: showExplanation,
  });

  const prompt = language === "en" ? question.prompt_en : question.prompt_pt;
  const questionNumber = index + 1;

  const handleChoice = useCallback(
    (choice: "true" | "false") => {
      setUserChoice(choice);
    },
    [],
  );

  const handleReveal = useCallback(() => {
    if (!userChoice) return;
    setShowExplanation(true);
  }, [userChoice]);

  const canReveal = userChoice !== null;

  return (
    <Card data-testid={`question-card-${question.id}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          <span className="text-sm font-bold text-muted-foreground">
            {questionNumber}.
          </span>
          <div className="flex-1">
            <p className="text-base font-medium leading-relaxed">
              {prompt}
            </p>
            {question.tricky && (
              <Badge
                variant="destructive"
                className="mt-2"
                data-testid={`question-tricky-${question.id}`}
              >
                {t("study.trickyBadge")}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* True / False buttons */}
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {t("study.answerPrompt")}
          </span>
          <div className="flex gap-2" data-testid={`question-choices-${question.id}`}>
            <Button
              size="sm"
              variant={userChoice === "true" ? "default" : "outline"}
              onClick={() => handleChoice("true")}
              data-testid={`question-true-${question.id}`}
              aria-pressed={userChoice === "true"}
            >
              {t("common.buttons.true")}
            </Button>
            <Button
              size="sm"
              variant={userChoice === "false" ? "default" : "outline"}
              onClick={() => handleChoice("false")}
              data-testid={`question-false-${question.id}`}
              aria-pressed={userChoice === "false"}
            >
              {t("common.buttons.false")}
            </Button>
          </div>
        </div>

        {/* Show explanation button */}
        {!showExplanation ? (
          <Button
            variant="secondary"
            size="sm"
            disabled={!canReveal}
            onClick={handleReveal}
            data-testid={`question-reveal-${question.id}`}
          >
            {canReveal
              ? t("common.buttons.showExplanation")
              : t("study.selectAnswerFirst")}
          </Button>
        ) : (
          <div data-testid={`question-explanation-${question.id}`}>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowExplanation(false)}
              className="mb-3"
            >
              {t("common.buttons.hideExplanation")}
            </Button>

            {detailLoading ? (
              <Skeleton className="h-24 rounded-md" />
            ) : detail ? (
              <ExplanationReveal
                detail={detail}
                userChoice={userChoice}
                language={language}
                t={t}
              />
            ) : (
              <p className="text-sm text-muted-foreground">
                {t("study.noQuestions")}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Explanation Reveal ─────────────────────────────────────────────────────

interface ExplanationRevealProps {
  detail: QuestionDetail;
  userChoice: UserChoice;
  language: "en" | "pt";
  t: (key: string, opts?: Record<string, unknown>) => string;
}

function ExplanationReveal({
  detail,
  userChoice,
  language,
  t,
}: ExplanationRevealProps) {
  const correctAnswer = detail.answer_en as "true" | "false";
  const isCorrect = userChoice === correctAnswer;

  const answerLabel =
    correctAnswer === "true"
      ? t("common.buttons.true")
      : t("common.buttons.false");

  const userLabel =
    userChoice === "true"
      ? t("common.buttons.true")
      : t("common.buttons.false");

  const explanation =
    language === "en" ? detail.explanation_en : detail.explanation_pt;

  return (
    <div className="space-y-3 rounded-md border p-4 bg-muted/30">
      {/* Result badge */}
      <div className="flex items-center gap-2">
        <Badge variant={isCorrect ? "default" : "destructive"}>
          {isCorrect ? t("study.correct") : t("study.incorrect")}
        </Badge>
      </div>

      {/* Answers */}
      <div className="space-y-1 text-sm">
        <p className="text-muted-foreground">
          {t("study.yourAnswer", { answer: userLabel })}
        </p>
        <p className="font-medium text-foreground">
          {t("study.correctAnswer", { answer: answerLabel })}
        </p>
      </div>

      {/* Explanation */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {t("study.explanation")}
        </p>
        <p className="mt-1 text-sm leading-relaxed text-foreground">
          {explanation}
        </p>
      </div>
    </div>
  );
}
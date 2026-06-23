import { useState, useEffect, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "@tanstack/react-router";
import { api } from "@/lib/api";
import { useUIStore } from "@/store/ui";
import { useMockTestStore } from "@/store/mock-test";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import type { AnswerItem, UserAnswer } from "@/types";

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

interface MockTestRunnerProps {
  attemptId: number;
  paramAttemptId: string;
}

export function MockTestRunner({ attemptId, paramAttemptId }: MockTestRunnerProps) {
  const { t } = useTranslation();
  const language = useUIStore((s) => s.language);
  const navigate = useNavigate();
  const { questions, timeLimitSeconds, setResult } = useMockTestStore();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, UserAnswer>>({});
  const [remainingSeconds, setRemainingSeconds] = useState(timeLimitSeconds);
  const [submitting, setSubmitting] = useState(false);
  const [showTimeoutWarning, setShowTimeoutWarning] = useState(false);
  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submittedRef = useRef(false);

  const totalQuestions = questions.length;
  const answeredCount = Object.keys(answers).length;
  const allAnswered = answeredCount === totalQuestions;
  const currentQuestion = questions[currentIndex];
  const currentAnswer = currentQuestion ? answers[currentQuestion.id] : undefined;

  useEffect(() => {
    if (String(attemptId) !== paramAttemptId) {
      navigate({ to: "/mock-test" });
    }
  }, [attemptId, paramAttemptId, navigate]);

  useEffect(() => {
    if (import.meta.env.VITE_API_MOCK === "true" && attemptId) {
      const correct = api.mockTests.getCorrectAnswers(attemptId);
      if (correct) {
        (window as unknown as Record<string, unknown>).__mockTestCorrectAnswers = correct;
      }
    }
  }, [attemptId]);

  useEffect(() => {
    if (!attemptId) return;
    const interval = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [attemptId]);

  useEffect(() => {
    if (!attemptId) return;
    const interval = setInterval(async () => {
      try {
        const result = await api.mockTests.getTimeout(attemptId);
        setRemainingSeconds(result.remaining_seconds);
        if (result.timed_out && !submittedRef.current) {
          setShowTimeoutWarning(true);
          handleSubmit(true);
        }
      } catch {
        // silent
      }
    }, 30_000);
    return () => clearInterval(interval);
  }, [attemptId]);

  useEffect(() => {
    if (remainingSeconds === 0 && !submittedRef.current) {
      setShowTimeoutWarning(true);
      handleSubmit(true);
    }
  }, [remainingSeconds]);

  const handleAnswer = useCallback((answer: UserAnswer) => {
    if (!currentQuestion) return;
    setAnswers((prev) => ({ ...prev, [currentQuestion.id]: answer }));
  }, [currentQuestion]);

  const goNext = useCallback(() => {
    setCurrentIndex((prev) => Math.min(prev + 1, totalQuestions - 1));
  }, [totalQuestions]);

  const goPrev = useCallback(() => {
    setCurrentIndex((prev) => Math.max(prev - 1, 0));
  }, []);

  const handleSubmit = useCallback(async (isTimeout = false) => {
    if (submittedRef.current) return;
    if (!attemptId) return;
    submittedRef.current = true;
    setSubmitting(true);

    const answerItems: AnswerItem[] = questions.map((q) => ({
      question_id: q.id,
      user_answer: answers[q.id] ?? "false",
      time_spent_ms: null,
    }));

    try {
      const result = await api.mockTests.submit(attemptId, { answers: answerItems });
      setResult(result);
      navigate({
        to: "/mock-test/$attemptId/result",
        params: { attemptId: String(attemptId) },
      });
    } catch (e) {
      submittedRef.current = false;
      setSubmitting(false);
      if (!isTimeout) {
        setError(e instanceof Error ? e.message : "Failed to submit");
      }
    }
  }, [attemptId, questions, answers, setResult, navigate]);

  if (!currentQuestion) {
    return (
      <div className="container mx-auto py-8">
        <p className="text-muted-foreground" data-testid="no-attempt">
          {t("mockTest.noAttempt")}
        </p>
        <Button asChild variant="outline" className="mt-4">
          <a href="/mock-test">{t("mockTest.backToStart")}</a>
        </Button>
      </div>
    );
  }

  const prompt = language === "en" ? currentQuestion.prompt_en : currentQuestion.prompt_pt;
  const progressValue = (answeredCount / totalQuestions) * 100;
  const isLow = remainingSeconds <= 60;

  return (
    <div className="container mx-auto py-4 max-w-3xl">
      <div className="flex items-center justify-between mb-4" data-testid="runner-header">
        <h1 data-testid="page-title" className="text-xl font-bold">
          {t("mockTest.runnerTitle")}
        </h1>
        <div className="flex items-center gap-3">
          <span
            className={`text-lg font-mono font-bold ${isLow ? "text-destructive" : "text-foreground"}`}
            data-testid="timer-display"
          >
            {formatTime(remainingSeconds)}
          </span>
        </div>
      </div>

      <div className="mb-6 space-y-1" data-testid="progress-section">
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span data-testid="progress-text">
            {t("mockTest.questionOf", { current: currentIndex + 1, total: totalQuestions })}
          </span>
          <span data-testid="answered-count">
            {t("mockTest.answered", { answered: answeredCount, total: totalQuestions })}
          </span>
        </div>
        <Progress value={progressValue} data-testid="progress-bar" />
      </div>

      {showTimeoutWarning && (
        <div
          className="mb-4 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive"
          data-testid="timeout-warning"
        >
          {t("mockTest.timeoutWarning")}
        </div>
      )}

      {error && (
        <p className="mb-4 text-sm text-destructive" data-testid="submit-error">
          {error}
        </p>
      )}

      <Card data-testid="question-card" className="mb-6">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3 mb-6">
            <span className="text-sm font-bold text-muted-foreground shrink-0">
              {currentIndex + 1}.
            </span>
            <p className="text-base font-medium leading-relaxed flex-1" data-testid="question-prompt">
              {prompt}
            </p>
          </div>

          <div className="flex gap-3" data-testid="question-choices">
            <Button
              size="lg"
              variant={currentAnswer === "true" ? "default" : "outline"}
              onClick={() => handleAnswer("true")}
              data-testid="answer-true"
              aria-pressed={currentAnswer === "true"}
              className="flex-1"
            >
              {t("common.buttons.true")}
            </Button>
            <Button
              size="lg"
              variant={currentAnswer === "false" ? "default" : "outline"}
              onClick={() => handleAnswer("false")}
              data-testid="answer-false"
              aria-pressed={currentAnswer === "false"}
              className="flex-1"
            >
              {t("common.buttons.false")}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center justify-between gap-4" data-testid="runner-nav">
        <Button
          variant="outline"
          onClick={goPrev}
          disabled={currentIndex === 0}
          data-testid="nav-prev"
        >
          {t("common.buttons.previous")}
        </Button>

        <div className="flex items-center gap-2">
          {submitting ? (
            <Button disabled size="lg" data-testid="submitting-btn">
              <Skeleton className="h-4 w-20" />
            </Button>
          ) : showSubmitConfirm ? (
            <>
              <Button
                variant="destructive"
                size="lg"
                onClick={() => handleSubmit(false)}
                data-testid="submit-confirm-yes"
              >
                {t("mockTest.submitConfirmYes")}
              </Button>
              <Button
                variant="outline"
                size="lg"
                onClick={() => setShowSubmitConfirm(false)}
                data-testid="submit-confirm-no"
              >
                {t("mockTest.submitConfirmNo")}
              </Button>
            </>
          ) : (
            <Button
              size="lg"
              variant={allAnswered ? "default" : "secondary"}
              disabled={!allAnswered}
              onClick={() => setShowSubmitConfirm(true)}
              data-testid="submit-btn"
            >
              {allAnswered
                ? t("mockTest.submitExam")
                : t("mockTest.submitDisabled")}
            </Button>
          )}
        </div>

        <Button
          variant="outline"
          onClick={goNext}
          disabled={currentIndex === totalQuestions - 1}
          data-testid="nav-next"
        >
          {t("common.buttons.next")}
        </Button>
      </div>

      <div className="mt-6 flex flex-wrap gap-1.5 justify-center" data-testid="question-dots">
        {questions.map((q, i) => (
          <button
            key={q.id}
            onClick={() => setCurrentIndex(i)}
            className={`h-3 w-3 rounded-full transition-colors ${
              i === currentIndex
                ? "bg-primary"
                : answers[q.id]
                  ? "bg-primary/50"
                  : "bg-muted"
            }`}
            aria-label={`Question ${i + 1}`}
            data-testid={`dot-${i}`}
          />
        ))}
      </div>
    </div>
  );
}

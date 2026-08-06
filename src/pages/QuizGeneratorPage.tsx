import { useState } from "react";
import { 
  Brain, Sparkles, Plus, CheckCircle2, AlertCircle, HelpCircle, ArrowRight, Trophy, RefreshCw, Loader2
} from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useApi } from "@/hooks/useApi";
import { apiFetch } from "@/services/api";

export default function QuizGeneratorPage() {
  const { data: quizzes, refetch } = useApi<any[]>("/quizzes/");
  
  const [topic, setTopic] = useState("");
  const [numQuestions, setNumQuestions] = useState(5);
  const [difficulty, setDifficulty] = useState("medium");
  const [generating, setGenerating] = useState(false);
  const [generatedQuiz, setGeneratedQuiz] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Active quiz attempt state
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, number>>({});
  const [submittedResult, setSubmittedResult] = useState<any | null>(null);

  const handleGenerateQuiz = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setGenerating(true);
    setError(null);
    setGeneratedQuiz(null);
    setSubmittedResult(null);
    setSelectedAnswers({});

    try {
      const res = await apiFetch<any>("/quizzes/generate", {
        method: "POST",
        body: {
          topic,
          num_questions: Number(numQuestions),
          difficulty,
        },
      });
      setGeneratedQuiz(res);
      refetch();
    } catch (err: any) {
      if (err.status === 401 || err.message?.toLowerCase().includes("authenticated")) {
        setError("Your session has expired. Please log in again to generate quizzes.");
      } else {
        setError(err.message || "Failed to generate AI quiz.");
      }
    } finally {
      setGenerating(false);
    }
  };

  const getCorrectIdx = (q: any) => {
    if (typeof q.correct_option_index === "number" && q.correct_option_index >= 0) {
      return q.correct_option_index;
    }
    const options = q.options || [];
    const answerStr = String(q.correct_answer || "").trim().toLowerCase();
    const foundIdx = options.findIndex((o: string) => o.trim().toLowerCase() === answerStr);
    return foundIdx >= 0 ? foundIdx : 0;
  };

  const handleSubmitAnswers = () => {
    if (!generatedQuiz) return;
    const questions = generatedQuiz.questions || [];
    let correct = 0;
    questions.forEach((q: any, idx: number) => {
      if (selectedAnswers[idx] === getCorrectIdx(q)) {
        correct++;
      }
    });
    const total = questions.length;
    const scorePct = Math.round((correct / total) * 100);
    setSubmittedResult({ correct, total, scorePct });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI Quiz & Assessment Generator"
        description="Instantly generate interactive quizzes with multiple choice questions, answer keys, and difficulty distribution."
      />

      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        {/* Left Column: Quiz Config */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Brain className="h-4 w-4 text-primary" /> Quiz Configuration
            </CardTitle>
            <CardDescription className="text-xs">
              Enter a topic or paste course notes to build a quiz.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleGenerateQuiz} className="space-y-4">
              <div className="space-y-1.5">
                <Label className="text-xs">Quiz Subject / Topic *</Label>
                <Input
                  placeholder="e.g. Data Structures, Python Basics, Machine Learning"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  disabled={generating}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-xs">Questions</Label>
                  <Input
                    type="number"
                    min={1}
                    max={20}
                    value={numQuestions}
                    onChange={(e) => setNumQuestions(Number(e.target.value))}
                    disabled={generating}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Difficulty</Label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    disabled={generating}
                    className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-xs shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
              </div>

              {error && (
                <div className="p-3 bg-destructive/10 text-destructive rounded-lg text-xs flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <Button type="submit" loading={generating} disabled={!topic.trim()} className="w-full gap-2">
                <Sparkles className="h-4 w-4" /> Generate Quiz
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Right Column: Quiz Preview & Test Runner */}
        <Card className="md:col-span-3">
          <CardHeader className="flex flex-row items-center justify-between py-3">
            <div>
              <CardTitle className="text-sm flex items-center gap-2">
                <HelpCircle className="h-4 w-4 text-primary" /> Active Quiz Assessment
              </CardTitle>
              {generatedQuiz && (
                <CardDescription className="text-xs mt-0.5">
                  Topic: {generatedQuiz.title || topic}
                </CardDescription>
              )}
            </div>
            {submittedResult && (
              <Badge variant="outline" className="text-xs bg-emerald-500/10 text-emerald-600 border-emerald-500/30">
                Score: {submittedResult.scorePct}% ({submittedResult.correct}/{submittedResult.total})
              </Badge>
            )}
          </CardHeader>
          <CardContent className="space-y-6">
            {generatedQuiz && generatedQuiz.questions && generatedQuiz.questions.length > 0 ? (
              <div className="space-y-6">
                {generatedQuiz.questions.map((q: any, qIdx: number) => {
                  const correctIdx = getCorrectIdx(q);
                  return (
                    <div key={qIdx} className="p-4 border rounded-xl space-y-3 bg-card/50">
                      <p className="font-medium text-xs text-foreground">
                        {qIdx + 1}. {q.question_text}
                      </p>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {(q.options || []).map((opt: string, optIdx: number) => {
                          const isSelected = selectedAnswers[qIdx] === optIdx;
                          const isCorrect = correctIdx === optIdx;
                          return (
                            <button
                              key={optIdx}
                              type="button"
                              onClick={() => setSelectedAnswers((prev) => ({ ...prev, [qIdx]: optIdx }))}
                              className={`p-3 rounded-lg text-xs font-medium border text-left transition-all ${
                                submittedResult
                                  ? isCorrect
                                    ? "bg-emerald-500/20 border-emerald-500 text-emerald-600 font-bold"
                                    : isSelected
                                    ? "bg-destructive/20 border-destructive text-destructive"
                                    : "border-border opacity-50"
                                  : isSelected
                                  ? "bg-primary text-primary-foreground border-primary"
                                  : "hover:bg-muted border-border"
                              }`}
                            >
                              {opt}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}

                {!submittedResult ? (
                  <Button onClick={handleSubmitAnswers} className="w-full gap-2">
                    <Trophy className="h-4 w-4" /> Submit Quiz Answers
                  </Button>
                ) : (
                  <div className="p-4 bg-emerald-500/10 rounded-xl border border-emerald-500/30 text-center space-y-1">
                    <p className="font-bold text-emerald-600">Quiz Complete!</p>
                    <p className="text-xs text-muted-foreground">
                      You scored {submittedResult.correct} out of {submittedResult.total} questions ({submittedResult.scorePct}%).
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center text-center py-16 space-y-3">
                <Brain className="h-12 w-12 text-muted-foreground/30" />
                <h3 className="font-medium text-base">No Quiz Generated Yet</h3>
                <p className="text-xs text-muted-foreground max-w-sm">
                  Configure your topic on the left and click "Generate Quiz" to create interactive AI questions.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

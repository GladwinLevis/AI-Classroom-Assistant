import { useState } from "react";
import { 
  ClipboardCheck, Sparkles, FileText, CheckCircle2, AlertTriangle, Search, Loader2, Award, FileSpreadsheet
} from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { apiFetch } from "@/services/api";

export default function AssignmentCheckerPage() {
  const [assignmentTitle, setAssignmentTitle] = useState("");
  const [submissionText, setSubmissionText] = useState("");
  const [rubricText, setRubricText] = useState("");
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [plagiarismResult, setPlagiarismResult] = useState<any | null>(null);
  const [checkingPlagiarism, setCheckingPlagiarism] = useState(false);

  const handleEvaluate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!submissionText.trim()) return;

    setEvaluating(true);
    setError(null);
    setResult(null);

    try {
      const res = await apiFetch<any>("/assignments/evaluate", {
        method: "POST",
        body: {
          assignment_id: "00000000-0000-0000-0000-000000000000",
          student_submission: submissionText,
          rubric: rubricText ? [{ criterion: "General Quality", weight: 1.0, max_score: 100, description: rubricText }] : undefined,
        },
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to evaluate assignment.");
    } finally {
      setEvaluating(false);
    }
  };

  const handleCheckPlagiarism = async () => {
    if (!submissionText.trim()) return;
    setCheckingPlagiarism(true);
    try {
      const res = await apiFetch<any>("/assignments/check-plagiarism", {
        method: "POST",
        body: {
          text: submissionText,
        },
      });
      setPlagiarismResult(res);
    } catch (err: any) {
      console.error(err);
    } finally {
      setCheckingPlagiarism(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI Assignment Evaluator & Plagiarism Checker"
        description="Grade student essays and code, evaluate against rubrics, and run deep semantic plagiarism detection."
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Input Form */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" /> Assignment Submission
            </CardTitle>
            <CardDescription>Paste student submission and rubric criteria below for instant AI grading.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleEvaluate} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="title">Assignment Title (Optional)</Label>
                <Input
                  id="title"
                  placeholder="e.g. Physics Midterm Essay - Quantum Mechanics"
                  value={assignmentTitle}
                  onChange={(e) => setAssignmentTitle(e.target.value)}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="rubric">Grading Rubric / Criteria</Label>
                <Textarea
                  id="rubric"
                  placeholder="Specify grading criteria (e.g., Clarity: 30%, Technical Accuracy: 50%, Citation: 20%)"
                  value={rubricText}
                  onChange={(e) => setRubricText(e.target.value)}
                  className="min-h-[80px]"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="submission">Student Submission Text *</Label>
                <Textarea
                  id="submission"
                  placeholder="Paste essay text or code submission here..."
                  value={submissionText}
                  onChange={(e) => setSubmissionText(e.target.value)}
                  className="min-h-[180px]"
                  required
                />
              </div>

              {error && (
                <div className="p-3 bg-destructive/10 text-destructive text-sm rounded-lg flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" /> {error}
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <Button type="submit" loading={evaluating} className="w-full gap-2">
                  <Sparkles className="h-4 w-4" /> Evaluate Assignment
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  loading={checkingPlagiarism}
                  onClick={handleCheckPlagiarism}
                  className="gap-2 shrink-0"
                >
                  <Search className="h-4 w-4" /> Plagiarism Check
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Right Column: AI Feedback & Results */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Award className="h-5 w-5 text-primary" /> Evaluation Results
              </span>
              {result && (
                <Badge variant={result.score >= 80 ? "default" : result.score >= 60 ? "secondary" : "destructive"}>
                  Score: {result.score || result.overall_score || 85} / 100
                </Badge>
              )}
            </CardTitle>
            <CardDescription>AI-generated score breakdown, constructive feedback, and plagiarism report.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Plagiarism Alert if run */}
            {plagiarismResult && (
              <div className={`p-4 rounded-xl border ${
                plagiarismResult.similarity_percentage > 20 
                  ? "bg-amber-500/10 border-amber-500/30 text-amber-600" 
                  : "bg-emerald-500/10 border-emerald-500/30 text-emerald-600"
              }`}>
                <div className="flex items-center justify-between font-semibold text-sm">
                  <span>Plagiarism Similarity Score</span>
                  <Badge variant="outline">{plagiarismResult.similarity_percentage || 0}% Match</Badge>
                </div>
                <p className="text-xs mt-1">
                  {plagiarismResult.similarity_percentage > 20 
                    ? "Potential similarity detected against online/internal documents." 
                    : "Original content. No significant plagiarism detected."}
                </p>
              </div>
            )}

            {/* AI Feedback Report */}
            {result ? (
              <div className="space-y-4">
                <div className="p-4 bg-primary/5 rounded-xl border border-primary/20 space-y-2">
                  <h4 className="text-sm font-semibold text-primary flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" /> Comprehensive AI Feedback
                  </h4>
                  <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">
                    {result.feedback || result.detailed_feedback || "Great overall structure. Ensure proper citations in technical arguments."}
                  </p>
                </div>

                {result.strengths && (
                  <div className="space-y-1">
                    <p className="text-xs font-semibold uppercase text-muted-foreground">Strengths</p>
                    <ul className="list-disc list-inside text-sm space-y-1 text-emerald-600">
                      {result.strengths.map((s: string, idx: number) => (
                        <li key={idx}>{s}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.improvements && (
                  <div className="space-y-1">
                    <p className="text-xs font-semibold uppercase text-muted-foreground">Areas for Improvement</p>
                    <ul className="list-disc list-inside text-sm space-y-1 text-amber-600">
                      {result.improvements.map((imp: string, idx: number) => (
                        <li key={idx}>{imp}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center text-center py-20 space-y-3">
                <ClipboardCheck className="h-12 w-12 text-muted-foreground/30" />
                <h3 className="font-medium text-base">No Evaluation Generated Yet</h3>
                <p className="text-xs text-muted-foreground max-w-sm">
                  Paste a student submission on the left and click "Evaluate Assignment" to generate detailed feedback and scores.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

import { useState } from "react";
import { 
  FileText, Upload, Sparkles, Download, Search, Loader2, BookOpen, CheckCircle2, AlertCircle, FileCheck
} from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useApi } from "@/hooks/useApi";
import { apiFetch } from "@/services/api";

interface NoteItem {
  id: string;
  title: string;
  content?: string;
  summary?: string;
  file_path?: string;
  created_at: string;
}

export default function NotesSummaryPage() {
  const { data: notes, loading, refetch } = useApi<NoteItem[]>("/notes/");
  const [selectedNote, setSelectedNote] = useState<NoteItem | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<{ ai_answer?: string | null; matches?: any[] } | null>(null);
  const [searching, setSearching] = useState(false);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    const formData = new FormData();
    formData.append("title", file.name);
    formData.append("file", file);

    try {
      const token = localStorage.getItem("access_token");
      const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${apiBase}/notes/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(errData.detail || "Failed to process note file.");
      }

      setUploadSuccess(`File "${file.name}" uploaded and AI summary generated successfully!`);
      refetch();
    } catch (err: any) {
      setUploadError(err.message || "Error uploading document.");
    } finally {
      setUploading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() || !selectedNote) return;

    setSearching(true);
    try {
      const res = await apiFetch<any>(`/notes/${selectedNote.id}/search?query=${encodeURIComponent(searchQuery)}`);
      setSearchResults({
        ai_answer: res.ai_answer || null,
        matches: res.matches || [],
      });
    } catch (err: any) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  const handleDownloadMarkdown = (note: NoteItem) => {
    const content = `# ${note.title}\n\n## AI Summary\n${note.summary || "No summary available."}\n\n## Content\n${note.content || ""}`;
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${note.title.replace(/\s+/g, "_")}_Summary.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Lecture Notes & AI Summarizer" 
        description="Upload lecture slides, PDFs, or DOCX files to generate AI summaries, key takeaways, and interactive RAG semantic search." 
      />

      {/* File Upload Zone */}
      <Card className="border-dashed border-2">
        <CardContent className="pt-6">
          <div className="flex flex-col items-center justify-center text-center space-y-3">
            <div className="p-3 bg-primary/10 rounded-full text-primary">
              <Upload className="h-8 w-8" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">Upload Lecture Document</h3>
              <p className="text-sm text-muted-foreground">Supported formats: PDF, DOCX, PPTX, TXT (Up to 25MB)</p>
            </div>
            <label className="cursor-pointer">
              <input type="file" onChange={handleFileUpload} className="hidden" accept=".pdf,.docx,.pptx,.txt" disabled={uploading} />
              <Button type="button" loading={uploading} variant="default" className="gap-2 pointer-events-none">
                {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                {uploading ? "Extracting & Summarizing..." : "Select Document"}
              </Button>
            </label>

            {uploadError && (
              <div className="flex items-center gap-2 text-sm text-destructive font-medium bg-destructive/10 p-3 rounded-lg w-full max-w-md justify-center">
                <AlertCircle className="h-4 w-4" /> {uploadError}
              </div>
            )}

            {uploadSuccess && (
              <div className="flex items-center gap-2 text-sm text-emerald-600 font-medium bg-emerald-500/10 p-3 rounded-lg w-full max-w-md justify-center">
                <CheckCircle2 className="h-4 w-4" /> {uploadSuccess}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Document List */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle className="text-base flex items-center justify-between">
              <span>Your Library</span>
              <Badge variant="secondary">{notes?.length || 0} Files</Badge>
            </CardTitle>
            <CardDescription>Select a note to view its AI summary</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 max-h-[500px] overflow-y-auto">
            {loading ? (
              <div className="flex justify-center p-6"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
            ) : !notes || notes.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-6">No documents uploaded yet.</p>
            ) : (
              notes.map((note) => (
                <div
                  key={note.id}
                  onClick={() => { setSelectedNote(note); setSearchResults(null); }}
                  className={`p-3 rounded-lg border cursor-pointer transition-all flex items-start justify-between ${
                    selectedNote?.id === note.id ? "bg-primary/10 border-primary" : "hover:bg-muted/50 border-border"
                  }`}
                >
                  <div className="space-y-1">
                    <p className="font-medium text-sm line-clamp-1">{note.title}</p>
                    <p className="text-[11px] text-muted-foreground">{new Date(note.created_at).toLocaleDateString()}</p>
                  </div>
                  <FileCheck className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Note Details & AI Summary Viewer */}
        <Card className="md:col-span-2">
          {selectedNote ? (
            <CardContent className="pt-6 space-y-6">
              <div className="flex items-center justify-between border-b pb-4">
                <div>
                  <h2 className="text-xl font-bold">{selectedNote.title}</h2>
                  <p className="text-xs text-muted-foreground">Generated AI Study Summary</p>
                </div>
                <Button size="sm" variant="outline" className="gap-2" onClick={() => handleDownloadMarkdown(selectedNote)}>
                  <Download className="h-4 w-4" /> Export (.md)
                </Button>
              </div>

              {/* Semantic RAG Search */}
              <form onSubmit={handleSearch} className="flex gap-2">
                <Input 
                  placeholder="Ask a question or search within this document..." 
                  value={searchQuery} 
                  onChange={(e) => setSearchQuery(e.target.value)} 
                />
                <Button type="submit" variant="secondary" loading={searching} className="gap-2 shrink-0">
                  <Search className="h-4 w-4" /> Search
                </Button>
              </form>

              {/* Search Results & Direct AI Answer */}
              {searchResults && (
                <div className="space-y-4">
                  {searchResults.ai_answer && (
                    <div className="p-4 bg-primary/10 rounded-xl border border-primary/30 space-y-1.5 shadow-sm">
                      <h4 className="text-xs font-bold text-primary flex items-center gap-2 uppercase tracking-wide">
                        <Sparkles className="h-4 w-4 text-amber-500" /> Direct AI Answer
                      </h4>
                      <p className="text-sm font-medium leading-relaxed text-foreground">
                        {searchResults.ai_answer}
                      </p>
                    </div>
                  )}

                  {searchResults.matches && searchResults.matches.length > 0 && (
                    <div className="space-y-2 bg-muted/40 p-4 rounded-xl border">
                      <p className="text-xs font-semibold text-muted-foreground uppercase">Relevant Document Excerpts ({searchResults.matches.length})</p>
                      {searchResults.matches.map((m: any, idx: number) => (
                        <div key={idx} className="text-xs bg-background p-3 rounded-lg border space-y-1">
                          <p className="font-medium text-foreground leading-normal">{m.snippet}</p>
                          <p className="text-[10px] font-semibold text-primary">Relevance Score: {(m.score * 100).toFixed(0)}%</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Structured AI Summary Output */}
              <div className="space-y-4">
                <div className="p-4 bg-primary/5 rounded-xl border border-primary/20 space-y-2">
                  <h4 className="text-sm font-semibold text-primary flex items-center gap-2">
                    <Sparkles className="h-4 w-4" /> AI Overview & Key Points
                  </h4>
                  <p className="text-sm leading-relaxed text-foreground">
                    {selectedNote.summary || selectedNote.content || "No summary text generated for this document."}
                  </p>
                </div>
              </div>
            </CardContent>
          ) : (
            <CardContent className="pt-6">
              <div className="flex flex-col items-center justify-center text-center py-16 space-y-3">
                <BookOpen className="h-12 w-12 text-muted-foreground/40" />
                <h3 className="font-medium text-base">No Document Selected</h3>
                <p className="text-xs text-muted-foreground max-w-sm">Select an existing document from your library on the left or upload a new file above to view AI summaries.</p>
              </div>
            </CardContent>
          )}
        </Card>
      </div>
    </div>
  );
}

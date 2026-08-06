import { useState, useRef, useEffect } from "react";
import { 
  Send, Bot, User as UserIcon, Sparkles, Loader2, Plus, MessageSquare, BookOpen, Trash2
} from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useApi } from "@/hooks/useApi";
import { apiFetch } from "@/services/api";

interface Message {
  id?: string;
  sender: "user" | "bot";
  text: string;
  timestamp: string;
}

export default function ChatbotPage() {
  const { data: sessions, refetch: refetchSessions } = useApi<any[]>("/chat/sessions");
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "bot",
      text: "Hello! I am your AI Classroom Assistant. Ask me any question about your courses, lecture notes, quizzes, or assignments!",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [inputPrompt, setInputPrompt] = useState("");
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
    inputRef.current?.focus();
  }, [messages, sending]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputPrompt.trim() || sending) return;

    const userText = inputPrompt.trim();
    setInputPrompt("");
    const userMsg: Message = {
      sender: "user",
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setSending(true);

    try {
      const res = await apiFetch<any>("/chat/send", {
        method: "POST",
        body: {
          session_id: activeSessionId || undefined,
          message: userText,
        },
      });

      let rawBotResponse = res.response || res.message || "I have analyzed your query based on classroom course material.";
      if (typeof rawBotResponse === "string" && rawBotResponse.includes('{"text":')) {
        try {
          const matches = rawBotResponse.match(/\{"text":\s*"([^"]+)"[^\}]*\}/g);
          if (matches) {
            const extracted = matches.map(m => {
              try { return JSON.parse(m).text; } catch { return ""; }
            }).filter(Boolean).join(" ");
            if (extracted) rawBotResponse = extracted;
          }
        } catch {
          // ignore parse error
        }
      }

      const botMsg: Message = {
        sender: "bot",
        text: rawBotResponse,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const isAuthErr = err.status === 401 || err.message?.toLowerCase().includes("authenticated") || err.message?.toLowerCase().includes("unauthorized");
      const errorMsg: Message = {
        sender: "bot",
        text: isAuthErr
          ? "Your session has expired. Please log in again at /login to chat with the AI assistant."
          : `Error: ${err.message || "AI service unavailable."}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setSending(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI Academic Chatbot"
        description="24/7 AI Teaching Assistant trained on your course documents, notes, and academic syllabus."
      />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 h-[650px]">
        {/* Left Column: Chat Sessions */}
        <Card className="md:col-span-1 flex flex-col h-full">
          <CardHeader className="py-3 border-b">
            <CardTitle className="text-sm flex items-center justify-between">
              <span>Conversations</span>
              <Button size="icon" variant="ghost" className="h-7 w-7" onClick={() => { setMessages([]); setActiveSessionId(null); setTimeout(() => inputRef.current?.focus(), 50); }}>
                <Plus className="h-4 w-4" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-2 flex-1 overflow-y-auto space-y-1">
            {!sessions || sessions.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-6">No previous chat sessions.</p>
            ) : (
              sessions.map((s, idx) => (
                <div
                  key={s.id || idx}
                  onClick={() => { setActiveSessionId(s.id); setTimeout(() => inputRef.current?.focus(), 50); }}
                  className={`p-2.5 rounded-lg border text-xs cursor-pointer flex items-center gap-2 ${
                    activeSessionId === s.id ? "bg-primary/10 border-primary" : "hover:bg-muted border-border"
                  }`}
                >
                  <MessageSquare className="h-3.5 w-3.5 text-primary shrink-0" />
                  <span className="truncate flex-1">{s.title || `Session #${idx + 1}`}</span>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Right Column: Active Chat Area */}
        <Card className="md:col-span-3 flex flex-col h-full">
          <CardHeader className="py-3 border-b flex flex-row items-center justify-between">
            <CardTitle className="text-sm flex items-center gap-2">
              <Bot className="h-4 w-4 text-primary" /> AI Assistant
            </CardTitle>
            <Badge variant="outline" className="text-[10px] gap-1 bg-primary/5">
              <Sparkles className="h-3 w-3 text-amber-500" /> RAG Connected
            </Badge>
          </CardHeader>

          <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex gap-3 text-sm ${
                  m.sender === "user" ? "flex-row-reverse" : "flex-row"
                }`}
              >
                <div
                  className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${
                    m.sender === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {m.sender === "user" ? <UserIcon className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </div>

                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-2.5 border shadow-sm ${
                    m.sender === "user"
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-card text-card-foreground border-border"
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed text-sm">{m.text}</p>
                  <span className="text-[10px] opacity-60 mt-1 block text-right">
                    {m.timestamp}
                  </span>
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex gap-3 items-center text-sm text-muted-foreground">
                <div className="h-8 w-8 rounded-full bg-primary/10 text-primary flex items-center justify-center">
                  <Bot className="h-4 w-4 animate-spin" />
                </div>
                <p className="italic">AI is generating response...</p>
              </div>
            )}
            <div ref={messagesEndRef} />
          </CardContent>

          {/* Input Form */}
          <div className="p-3 border-t bg-card">
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <Input
                ref={inputRef}
                autoFocus
                placeholder="Ask any academic doubt or question..."
                value={inputPrompt}
                onChange={(e) => setInputPrompt(e.target.value)}
                disabled={sending}
                className="flex-1"
              />
              <Button type="submit" loading={sending} className="gap-2 shrink-0">
                <Send className="h-4 w-4" /> Send
              </Button>
            </form>
          </div>
        </Card>
      </div>
    </div>
  );
}

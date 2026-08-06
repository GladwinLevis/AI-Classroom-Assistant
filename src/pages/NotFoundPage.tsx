import { Link } from "react-router-dom";
import { Sparkles, Home } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background px-6 text-center">
      <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-gradient shadow-glow">
        <Sparkles className="h-7 w-7 text-white" />
      </span>
      <div>
        <p className="text-7xl font-extrabold text-gradient">404</p>
        <h1 className="mt-2 text-xl font-semibold">This page hasn't been taught yet</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          The page you're looking for doesn't exist or may have moved.
        </p>
      </div>
      <Button asChild>
        <Link to="/">
          <Home className="h-4 w-4" /> Back to home
        </Link>
      </Button>
    </div>
  );
}

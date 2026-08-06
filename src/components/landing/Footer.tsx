import { Sparkles, Twitter, Linkedin, Youtube } from "lucide-react";

const columns = [
  {
    title: "Product",
    links: ["Features", "Pricing", "Integrations", "Changelog"],
  },
  {
    title: "Company",
    links: ["About us", "Careers", "Blog", "Press kit"],
  },
  {
    title: "Resources",
    links: ["Help center", "Community", "Guides", "API status"],
  },
  {
    title: "Legal",
    links: ["Privacy policy", "Terms of service", "Data processing", "Security"],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-border bg-muted/30">
      <div className="container py-14">
        <div className="grid gap-10 lg:grid-cols-[1.4fr_repeat(4,1fr)]">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-gradient">
                <Sparkles className="h-5 w-5 text-white" />
              </span>
              <span className="font-bold">AI Classroom Assistant</span>
            </div>
            <p className="mt-4 max-w-xs text-sm text-muted-foreground">
              The calm, AI-native workspace for classrooms — attendance, notes, doubts and grading in one place.
            </p>
            <div className="mt-5 flex gap-3">
              {[Twitter, Linkedin, Youtube].map((Icon, i) => (
                <a
                  key={i}
                  href="#"
                  className="flex h-9 w-9 items-center justify-center rounded-lg border border-border text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                  aria-label="Social link"
                >
                  <Icon className="h-4 w-4" />
                </a>
              ))}
            </div>
          </div>

          {columns.map((col) => (
            <div key={col.title}>
              <p className="text-sm font-semibold">{col.title}</p>
              <ul className="mt-4 space-y-2.5">
                {col.links.map((link) => (
                  <li key={link}>
                    <a href="#" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border pt-6 text-xs text-muted-foreground sm:flex-row">
          <p>© {new Date().getFullYear()} AI Classroom Assistant. All rights reserved.</p>
          <p>Built for classrooms that move fast.</p>
        </div>
      </div>
    </footer>
  );
}

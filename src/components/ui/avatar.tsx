import { cn } from "@/utils/cn";

interface AvatarProps {
  name: string;
  src?: string;
  className?: string;
  size?: "sm" | "md" | "lg";
}

const sizeMap = { sm: "h-8 w-8 text-xs", md: "h-10 w-10 text-sm", lg: "h-16 w-16 text-lg" };

export function Avatar({ name, src, className, size = "md" }: AvatarProps) {
  const initials = name
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  if (src) {
    return <img src={src} alt={name} className={cn("rounded-full object-cover", sizeMap[size], className)} />;
  }

  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-full bg-brand-gradient font-semibold text-white shrink-0",
        sizeMap[size],
        className
      )}
      role="img"
      aria-label={name}
    >
      {initials}
    </div>
  );
}

"use client";
import { useState, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { useActivityToast } from "@/hooks/use-activity-toast";

interface TaskButtonProps {
  label: ReactNode;
  loadingLabel?: string;
  onClick: () => Promise<{ error: boolean; response?: unknown }>;
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  disabled?: boolean;
  className?: string;
  onSuccess?: (res: unknown) => void;
}

/**
 * A button that shows a loading state while an async action is running,
 * then shows a success/error toast on completion.
 */
export function TaskButton({
  label,
  loadingLabel = "Running…",
  onClick,
  variant = "default",
  disabled = false,
  className,
  onSuccess,
}: TaskButtonProps) {
  const [loading, setLoading] = useState(false);
  const { toast } = useActivityToast();

  const handleClick = async () => {
    setLoading(true);
    try {
      const result = await onClick();
      if (result.error) {
        toast({
          variant: "destructive",
          title: "Error",
          description: String(result.response ?? "Operation failed"),
        });
      } else {
        toast({
          title: "Success",
          description: String(result.response ?? "Done"),
        });
        onSuccess?.(result.response);
      }
    } catch (exc) {
      toast({
        variant: "destructive",
        title: "Error",
        description: String(exc),
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      variant={variant}
      disabled={disabled || loading}
      className={className}
      onClick={handleClick}
    >
      {loading ? loadingLabel : label}
    </Button>
  );
}

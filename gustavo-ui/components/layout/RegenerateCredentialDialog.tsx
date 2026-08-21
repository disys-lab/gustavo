"use client";
import { useState } from "react";
import { KeyRound, Copy, Check } from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { regenerateMyToken } from "@/lib/api/users";
import { copyToClipboard } from "@/lib/utils";

export function RegenerateCredentialDialog() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [credential, setCredential] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (!next) {
      setCredential(null);
      setError(null);
      setCopied(false);
    }
  };

  const handleRegenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await regenerateMyToken();
      if (res.error) {
        setError(String(res.response));
      } else {
        setCredential(res.response.credential);
      }
    } catch (exc) {
      setError(String(exc));
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!credential) return;
    const ok = await copyToClipboard(credential);
    if (ok) {
      setCopied(true);
    } else {
      setError("Copy failed — select the text above and copy it manually.");
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <button
        onClick={() => setOpen(true)}
        className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium text-gray-400 hover:bg-gray-50 hover:text-gray-700 transition-colors text-left"
      >
        <KeyRound className="h-4 w-4 shrink-0" />
        My credential
      </button>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Regenerate my access credential</DialogTitle>
          <DialogDescription>
            This immediately invalidates your current credential. You&apos;ll need to
            update anywhere it&apos;s saved.
          </DialogDescription>
        </DialogHeader>

        {!credential && (
          <>
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <DialogFooter>
              <Button onClick={handleRegenerate} disabled={loading}>
                {loading ? "Generating…" : "Generate new credential"}
              </Button>
            </DialogFooter>
          </>
        )}

        {credential && (
          <>
            <Alert>
              <AlertDescription>
                Copy this now — it won&apos;t be shown again.
              </AlertDescription>
            </Alert>
            <div className="flex items-center gap-2 rounded-md border bg-gray-50 px-3 py-2">
              <code className="flex-1 break-all text-sm">{credential}</code>
              <Button size="sm" variant="ghost" onClick={handleCopy}>
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

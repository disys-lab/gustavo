"use client";
import { Download } from "lucide-react";
import { downloadWorkerConfig } from "@/lib/api/config";
import { useActivityToast } from "@/hooks/use-activity-toast";

export function DownloadWorkerConfigButton() {
  const { toast } = useActivityToast();

  const handleDownload = async () => {
    try {
      const text = await downloadWorkerConfig();
      const blob = new Blob([text], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "worker.env";
      a.click();
      URL.revokeObjectURL(url);
    } catch (exc) {
      toast({ variant: "destructive", title: "Download failed", description: String(exc) });
    }
  };

  return (
    <button
      onClick={handleDownload}
      className="w-full flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium text-gray-400 hover:bg-gray-50 hover:text-gray-700 transition-colors text-left"
    >
      <Download className="h-4 w-4 shrink-0" />
      Worker config
    </button>
  );
}

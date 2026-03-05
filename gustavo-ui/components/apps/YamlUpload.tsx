"use client";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { parseYaml } from "@/lib/api/apps";

interface YamlUploadProps {
  onParsed: (config: Record<string, unknown>) => void;
}

export function YamlUpload({ onParsed }: YamlUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const res = await parseYaml(file);
      if (!res.error) {
        onParsed(res.response as Record<string, unknown>);
      } else {
        setError(String(res.response));
      }
    } catch (exc) {
      setError(String(exc));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      <input
        ref={inputRef}
        type="file"
        accept=".yml,.yaml"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) handleFile(f);
        }}
      />
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={loading}
        onClick={() => inputRef.current?.click()}
      >
        {loading ? "Parsing…" : "Upload YAML"}
      </Button>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}

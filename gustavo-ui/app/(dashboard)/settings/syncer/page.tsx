"use client";
import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { useConfig } from "@/lib/context/ConfigContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useActivityToast } from "@/hooks/use-activity-toast";
import { Alert, AlertDescription } from "@/components/ui/alert";
import * as jsYaml from "js-yaml";

// Monaco editor is ESM-only — load client-side only
const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

export default function SyncerConfigPage() {
  const { config } = useConfig();
  const { toast } = useActivityToast();

  const [configPath, setConfigPath] = useState("");
  const [mappingPath, setMappingPath] = useState("");
  const [configContent, setConfigContent] = useState("# dregsy config YAML");
  const [mappingContent, setMappingContent] = useState("# dregsy mapping YAML");
  const [parseError, setParseError] = useState<string | null>(null);

  useEffect(() => {
    if (config.DREGSY_CONFIG_FILE_PATH) setConfigPath(config.DREGSY_CONFIG_FILE_PATH);
    if (config.DREGSY_MAPPING_FILE_PATH) setMappingPath(config.DREGSY_MAPPING_FILE_PATH);
  }, [config]);

  const validateYaml = (content: string): string | null => {
    try {
      jsYaml.load(content);
      return null;
    } catch (exc) {
      return String(exc);
    }
  };

  const handleConfigChange = (value: string | undefined) => {
    const v = value ?? "";
    setConfigContent(v);
    setParseError(validateYaml(v));
  };

  const handleMappingChange = (value: string | undefined) => {
    const v = value ?? "";
    setMappingContent(v);
    const err = validateYaml(v);
    if (err) setParseError(err);
    else setParseError(null);
  };

  const handleSave = () => {
    const cfgErr = validateYaml(configContent);
    const mapErr = validateYaml(mappingContent);
    if (cfgErr || mapErr) {
      setParseError(cfgErr ?? mapErr);
      return;
    }
    // In a real flow: POST the YAML content to the API to write the files
    toast({ title: "Syncer config validated", description: "Use the Manager Services page to launch Syncer" });
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Syncer Configuration</h1>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <Label>DREGSY Config File Path</Label>
          <Input value={configPath} onChange={(e) => setConfigPath(e.target.value)} className="mt-1" placeholder="/path/to/dregsy_conf.yml" />
        </div>
        <div>
          <Label>DREGSY Mapping File Path</Label>
          <Input value={mappingPath} onChange={(e) => setMappingPath(e.target.value)} className="mt-1" placeholder="/path/to/mappings_list.yml" />
        </div>
      </div>

      {parseError && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{parseError}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">dregsy_conf.yml</CardTitle>
          </CardHeader>
          <CardContent>
            <MonacoEditor
              height="400px"
              language="yaml"
              value={configContent}
              onChange={handleConfigChange}
              options={{ minimap: { enabled: false }, fontSize: 13 }}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">mappings_list.yml</CardTitle>
          </CardHeader>
          <CardContent>
            <MonacoEditor
              height="400px"
              language="yaml"
              value={mappingContent}
              onChange={handleMappingChange}
              options={{ minimap: { enabled: false }, fontSize: 13 }}
            />
          </CardContent>
        </Card>
      </div>

      <div className="mt-6">
        <Button onClick={handleSave} disabled={!!parseError}>
          Validate & Save Paths
        </Button>
      </div>
    </div>
  );
}

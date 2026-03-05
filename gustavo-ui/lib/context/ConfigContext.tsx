"use client";
import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
import { getConfig, updateConfig } from "@/lib/api/config";
import type { PlatformConfig } from "@/lib/types/platform";

interface ConfigContextValue {
  config: Partial<PlatformConfig>;
  isLoaded: boolean;
  refresh: () => Promise<void>;
  save: (partial: Partial<PlatformConfig>) => Promise<{ error: boolean; message?: string }>;
}

const ConfigContext = createContext<ConfigContextValue | null>(null);

export function ConfigProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<Partial<PlatformConfig>>({});
  const [isLoaded, setIsLoaded] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const res = await getConfig();
      if (!res.error) {
        const cfg = res.response as Partial<PlatformConfig>;
        setConfig(cfg);
        // Optimistic cache in localStorage
        if (typeof window !== "undefined") {
          localStorage.setItem("gustavo_config", JSON.stringify(cfg));
        }
      }
    } catch {
      // Fall back to localStorage cache
      if (typeof window !== "undefined") {
        const cached = localStorage.getItem("gustavo_config");
        if (cached) setConfig(JSON.parse(cached));
      }
    } finally {
      setIsLoaded(true);
    }
  }, []);

  // Hydrate from localStorage first, then fetch from API
  useEffect(() => {
    if (typeof window !== "undefined") {
      const cached = localStorage.getItem("gustavo_config");
      if (cached) {
        try {
          setConfig(JSON.parse(cached));
        } catch {}
      }
    }
    refresh();
  }, [refresh]);

  const save = async (partial: Partial<PlatformConfig>) => {
    try {
      const res = await updateConfig(partial);
      if (!res.error) {
        const updated = res.response as Partial<PlatformConfig>;
        setConfig(updated);
        if (typeof window !== "undefined") {
          localStorage.setItem("gustavo_config", JSON.stringify(updated));
        }
        return { error: false };
      }
      return { error: true, message: String(res.response) };
    } catch (exc) {
      return { error: true, message: String(exc) };
    }
  };

  return (
    <ConfigContext.Provider value={{ config, isLoaded, refresh, save }}>
      {children}
    </ConfigContext.Provider>
  );
}

export function useConfig() {
  const ctx = useContext(ConfigContext);
  if (!ctx) throw new Error("useConfig must be used within ConfigProvider");
  return ctx;
}

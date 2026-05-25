"use client";

import { useEffect, useMemo, useState } from "react";

export type UiLanguage = "pt";

const LANGUAGE_STORAGE_KEY = "ilb.ui_language";

function readStoredLanguage(): UiLanguage {
  return "pt";
}

export function useLanguagePreference() {
  const [language, setLanguageState] = useState<UiLanguage>("pt");

  useEffect(() => {
    setLanguageState(readStoredLanguage());
  }, []);

  const setLanguage = (next: UiLanguage) => {
    setLanguageState(next);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(LANGUAGE_STORAGE_KEY, next);
      document.documentElement.lang = "pt-PT";
    }
  };

  return useMemo(
    () => ({
      language,
      languageLabel: language.toUpperCase(),
      setLanguage,
    }),
    [language],
  );
}

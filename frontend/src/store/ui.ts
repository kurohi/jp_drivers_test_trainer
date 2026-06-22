import { create } from "zustand";
import { persist, type PersistStorage } from "zustand/middleware";

type Language = "en" | "pt";
type Theme = "light" | "dark";

interface UIState {
  language: Language;
  theme: Theme;
  setLanguage: (lang: Language) => void;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

/** Custom storage that persists language and theme to separate localStorage keys */
const splitStorage: PersistStorage<UIState> = {
  getItem: () => {
    const langRaw = localStorage.getItem("jp-test-language");
    const themeRaw = localStorage.getItem("jp-test-theme");
    if (langRaw === null && themeRaw === null) return null;
    return {
      state: {
        language: langRaw ? JSON.parse(langRaw) : "en",
        theme: themeRaw ? JSON.parse(themeRaw) : "light",
      } as UIState,
      version: 0,
    };
  },
  setItem: (_name, value) => {
    localStorage.setItem(
      "jp-test-language",
      JSON.stringify(value.state.language),
    );
    localStorage.setItem("jp-test-theme", JSON.stringify(value.state.theme));
  },
  removeItem: () => {
    localStorage.removeItem("jp-test-language");
    localStorage.removeItem("jp-test-theme");
  },
};

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      language: "en",
      theme: "light",
      setLanguage: (language) => set({ language }),
      setTheme: (theme) => set({ theme }),
      toggleTheme: () =>
        set({ theme: get().theme === "light" ? "dark" : "light" }),
    }),
    {
      name: "jp-test-ui",
      storage: splitStorage,
    },
  ),
);
import { afterEach, beforeEach, vi } from "vitest";

const storage = new Map<string, string>();

const localStorageMock = {
  getItem: (key: string) => (storage.has(key) ? storage.get(key)! : null),
  setItem: (key: string, value: string) => {
    storage.set(key, value);
  },
  removeItem: (key: string) => {
    storage.delete(key);
  },
  clear: () => {
    storage.clear();
  },
};

beforeEach(() => {
  storage.clear();
  vi.stubGlobal("window", { localStorage: localStorageMock });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

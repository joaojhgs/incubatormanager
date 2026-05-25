const appMessages = {
  metadataTitle: "ILB Incubator",
  metadataDescription: "Plataforma de gestão ILB Incubator",
} as const;

export type AppI18nKey = keyof typeof appMessages;

export function tApp(key: AppI18nKey): string {
  return appMessages[key];
}

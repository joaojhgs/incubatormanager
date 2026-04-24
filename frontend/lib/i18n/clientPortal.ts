const clientMessages = {
  headerTitle: "Portal do cliente",
  homeIntro: "Área reservada às empresas incubadas.",
} as const;

export type ClientPortalI18nKey = keyof typeof clientMessages;

export function tClient(key: ClientPortalI18nKey): string {
  return clientMessages[key];
}

const authMessages = {
  loginTitle: "Iniciar sessão",
  loginIntro:
    "A autenticação via formulário será ligada ao serviço de identidade. Por agora, utilize o fluxo de desenvolvimento com JWT válido no cookie de atualização.",
  loginRoleHint: "Função na sessão (JWT):",
  loginNotSignedIn: "Sem sessão ativa no browser.",
} as const;

export type AuthI18nKey = keyof typeof authMessages;

export function tAuth(key: AuthI18nKey): string {
  return authMessages[key];
}

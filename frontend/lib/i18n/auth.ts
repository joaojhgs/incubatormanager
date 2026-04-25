const authMessages = {
  loginTitle: "Iniciar sessão",
  loginSubtitle: "Introduza o seu email e palavra-passe para continuar.",
  loginEmailLabel: "Email",
  loginPasswordLabel: "Palavra-passe",
  loginSubmit: "Entrar",
  fieldEmailRequired: "Indique o email.",
  fieldEmailInvalid: "Indique um email válido.",
  fieldPasswordRequired: "Indique a palavra-passe.",
  loginErrorInvalid: "Credenciais inválidas. Verifique o email e a palavra-passe.",
  loginErrorGeneric: "Não foi possível iniciar sessão. Tente novamente.",
  loginErrorUnreachable: "Serviço de autenticação indisponível.",
} as const;

export type AuthI18nKey = keyof typeof authMessages;

export function tAuth(key: AuthI18nKey): string {
  return authMessages[key];
}

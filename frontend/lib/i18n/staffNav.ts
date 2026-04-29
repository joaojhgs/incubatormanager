const staffMessages = {
  siderBrand: "ILB Incubator",
  headerWorkspace: "Portal interno",
  navDashboard: "Painel",
  navCompanies: "Empresas",
  navContracts: "Contratos",
  navFinance: "Finanças",
  navSpaces: "Espaços",
  navBookings: "Reservas",
  navInventory: "Inventário",
  navTickets: "Pedidos de suporte",
  navUsers: "Utilizadores",
  headerAccount: "Conta",
  headerLanguage: "Idioma",
  languagePt: "Português",
  languageEn: "English (em breve)",
  menuProfile: "Perfil",
  menuLogout: "Terminar sessão",
  breadcrumbHome: "Início",
  breadcrumbUserCreate: "Novo utilizador",
  pageHomeTitle: "Painel",
  pageHomeIntro: "Área reservada à equipa do incubador. Utilize o menu lateral para navegar.",
  pagePlaceholderBody: "Conteúdo em desenvolvimento.",
} as const;

export type StaffI18nKey = keyof typeof staffMessages;

export function tStaff(key: StaffI18nKey): string {
  return staffMessages[key];
}

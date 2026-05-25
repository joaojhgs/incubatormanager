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

  // Service status pages (finance/contracts/bookings/...) currently backed by service health.
  serviceHealthStatus: "Estado do serviço",
  serviceHealthUnknown: "Desconhecido",
  serviceHealthUp: "Disponível",
  serviceHealthDown: "Indisponível",
  serviceHealthLoading: "A carregar estado do serviço…",
  pageLoading: "A carregar…",

  // Tickets (staff view)
  ticketsListTitle: "Pedidos de suporte",
  ticketsColumnCompany: "Empresa",
  ticketsColumnSubject: "Assunto",
  ticketsColumnStatus: "Estado",
  ticketsColumnUpdatedAt: "Atualizado em",
  ticketsColumnOwner: "Criado por",
  ticketsEmpty: "Sem pedidos de suporte para apresentar.",
  ticketsLoadError: "Não foi possível carregar os pedidos de suporte.",
  ticketStatusOpen: "Aberto",
  ticketStatusInProgress: "Em curso",
  ticketStatusWaitingResponse: "A aguardar resposta",
  ticketStatusResolved: "Resolvido",
  ticketStatusClosed: "Fechado",
} as const;

export type StaffI18nKey = keyof typeof staffMessages;

export function tStaff(key: StaffI18nKey): string {
  return staffMessages[key];
}

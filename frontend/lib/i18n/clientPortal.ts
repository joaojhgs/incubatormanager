const clientMessages = {
  // Shell / navigation
  siderBrand: "ILB Incubator",
  headerTitle: "Portal do cliente",
  navDashboard: "Painel",
  navCompany: "A minha empresa",
  navContract: "O meu contrato",
  navPayments: "Pagamentos",
  navBookings: "Reservas",
  navSupport: "Suporte",
  headerAccount: "Conta",
  headerLanguage: "Idioma",
  languagePt: "Português",
  languageEn: "English (em breve)",
  menuProfile: "Perfil",
  menuLogout: "Terminar sessão",
  breadcrumbHome: "Início",

  // Dashboard
  pageHomeTitle: "Painel",
  welcomeBack: "Bem-vindo, {name}",
  companyLabel: "Empresa",
  contractStatusActive: "Ativo",
  contractStatusExpired: "Expirado",
  monthlyFee: "Mensalidade",
  monthlyFeeSubtitle: "Devido no dia 1 de cada mês",
  nextPayment: "Próximo pagamento",
  nextPaymentPending: "Pendente",
  nextPaymentPaid: "Pago",
  openTickets: "Pedidos abertos",
  openTicketsAwaiting: "A aguardar resposta",
  contractSummary: "Resumo do contrato",
  contractSpace: "Espaço",
  contractArea: "Área",
  contractRate: "Taxa",
  contractPeriod: "Período",
  contractMonthlyFee: "Mensalidade",
  viewFullContract: "Ver contrato completo",
  recentPayments: "Pagamentos recentes",
  viewAllPayments: "Ver todos os pagamentos",
  quickActions: "Ações rápidas",
  requestBooking: "Solicitar reserva",
  openTicket: "Abrir pedido de suporte",

  // Placeholder/service pages
  pageCompanyTitle: "A minha empresa",
  pageContractTitle: "O meu contrato",
  pagePaymentsTitle: "Pagamentos",
  pageBookingsTitle: "Reservas",
  pageSupportTitle: "Suporte",
  pagePlaceholderBody: "Conteúdo em desenvolvimento.",
  pageLoading: "A carregar…",
  pageLoadError: "Não foi possível carregar os dados.",
  pageNoCompany: "A sua conta de utilizador não está associada a uma empresa.",
  pageNoCompanyAction: "Contacte o administrador da incubadora.",
  serviceUnavailable: "Serviço indisponível no momento.",
  serviceHealthUp: "Disponível",
  serviceHealthDown: "Indisponível",
  serviceHealthUnknown: "Desconhecido",
  serviceHealthLoading: "A carregar estado do serviço…",
  serviceHealthUnavailable: "Serviço em construção",
  serviceHealthHint:
    "Esta página mostra o estado atual do serviço enquanto os fluxos de negócio ainda estão em implementação.",

  // Company page details
  companyFieldCompany: "Empresa",
  companyFieldTaxId: "NIF",
  companyFieldLegalRepresentative: "Representante legal",
  companyFieldPhone: "Telefone",
  companyFieldEmail: "Email",
  companyFieldAddress: "Morada",
  companyFieldSection: "Dados da empresa",

  // Tickets (client view)
  portalTicketsTitle: "Pedidos de suporte",
  portalTicketsColumnSubject: "Assunto",
  portalTicketsColumnStatus: "Estado",
  portalTicketsColumnUpdatedAt: "Atualizado em",
  portalTicketsEmpty: "Ainda não tem pedidos de suporte registados.",
  portalTicketsLoadError: "Não foi possível carregar os seus pedidos de suporte.",
  portalTicketRolePrefix: "Criado por",
} as const;

export type ClientPortalI18nKey = keyof typeof clientMessages;

export function tClient(key: ClientPortalI18nKey): string {
  return clientMessages[key];
}

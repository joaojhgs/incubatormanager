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

  // Placeholder pages
  pageCompanyTitle: "A minha empresa",
  pageContractTitle: "O meu contrato",
  pagePaymentsTitle: "Pagamentos",
  pageBookingsTitle: "Reservas",
  pageSupportTitle: "Suporte",
  pagePlaceholderBody: "Conteúdo em desenvolvimento.",
} as const;

export type ClientPortalI18nKey = keyof typeof clientMessages;

export function tClient(key: ClientPortalI18nKey): string {
  return clientMessages[key];
}

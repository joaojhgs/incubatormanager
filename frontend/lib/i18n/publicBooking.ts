const publicBookingMessages = {
  pageTitle: "Pedido público de reserva",
  pageIntro:
    "Submeta um pedido de reserva para análise pela equipa da incubadora. Receberá confirmação após aprovação.",
  companyIdLabel: "Empresa",
  companyIdHelp: "Identificador da empresa atribuído pela incubadora.",
  companyIdRequired: "Indique a empresa.",
  spaceIdLabel: "Espaço",
  spaceIdHelp: "Identificador do espaço pretendido.",
  spaceIdRequired: "Indique o espaço.",
  requesterNameLabel: "Nome do requerente",
  requesterNameRequired: "Indique o nome do requerente.",
  requesterEmailLabel: "Email do requerente",
  requesterEmailRequired: "Indique o email do requerente.",
  requesterEmailInvalid: "Indique um email válido.",
  requesterPhoneLabel: "Telefone do requerente",
  requesterPhoneRequired: "Indique o telefone do requerente.",
  startTimeLabel: "Início",
  startTimeRequired: "Indique a data e hora de início.",
  endTimeLabel: "Fim",
  endTimeRequired: "Indique a data e hora de fim.",
  quotedPriceLabel: "Valor estimado",
  quotedPriceRequired: "Indique o valor estimado.",
  notesLabel: "Notas",
  notesPlaceholder: "Contexto adicional para a equipa avaliar o pedido.",
  submit: "Submeter pedido",
  submitting: "A submeter…",
  success: "Pedido recebido. A equipa irá analisar a reserva.",
  error: "Não foi possível submeter o pedido.",
} as const;

export type PublicBookingI18nKey = keyof typeof publicBookingMessages;

export function tPublicBooking(key: PublicBookingI18nKey): string {
  return publicBookingMessages[key];
}

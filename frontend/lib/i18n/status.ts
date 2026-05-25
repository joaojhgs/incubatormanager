const statusMessages: Record<string, string> = {
  active: "Ativo",
  inactive: "Inativo",
  draft: "Rascunho",
  terminated: "Terminado",
  expired: "Expirado",
  pending: "Pendente",
  approved: "Aprovado",
  rejected: "Rejeitado",
  cancelled: "Cancelado",
  canceled: "Cancelado",
  completed: "Concluído",
  paid: "Pago",
  overdue: "Em atraso",
  available: "Disponível",
  reserved: "Reservado",
  occupied: "Ocupado",
  maintenance: "Manutenção",
  blocked: "Bloqueado",
  "in use": "Em utilização",
  assigned: "Atribuído",
  released: "Libertado",
  open: "Aberto",
  "in progress": "Em curso",
  "waiting response": "A aguardar resposta",
  resolved: "Resolvido",
  closed: "Fechado",
};

export function normalizeStatus(status: string): string {
  return status.trim().toLowerCase().replace(/[_-]+/g, " ").replace(/\s+/g, " ");
}

export function statusLabel(status: string): string {
  return statusMessages[normalizeStatus(status)] ?? status;
}

const userMessages = {
  listTitle: "Utilizadores",
  listSearchPlaceholder: "Pesquisar por e-mail ou nome",
  listOpenFilters: "Filtros",
  listDrawerTitle: "Filtrar lista",
  listFilterRoleLabel: "Função",
  listFilterRoleAll: "Todas",
  listFilterActiveLabel: "Estado",
  listFilterActiveAll: "Todos",
  listFilterActiveYes: "Ativos",
  listFilterActiveNo: "Inativos",
  listApplyFilters: "Aplicar",
  listClearFilters: "Limpar",
  listColumnEmail: "E-mail",
  listColumnName: "Nome",
  listColumnRole: "Função",
  listColumnStatus: "Estado",
  listStatusActive: "Ativo",
  listStatusInactive: "Inativo",
  listShowingPagination: "{from}-{to} de {total}",
  listLoadError: "Não foi possível carregar a lista de utilizadores.",
  listForbiddenTitle: "Acesso restrito",
  listForbiddenDescription:
    "A gestão de utilizadores está disponível apenas para o perfil de diretor de incubadora.",
  listForbiddenBack: "Voltar ao painel",
  roleFilterDirector: "Diretor",
  roleFilterManager: "Gestor",
  roleFilterCoordinator: "Coordenador",
  roleFilterStaff: "Equipa",
  roleFilterClient: "Cliente (empresa)",
} as const;

export type UsersI18nKey = keyof typeof userMessages;

const roleLabelKeyByRole: Partial<Record<string, UsersI18nKey>> = {
  director: "roleFilterDirector",
  manager: "roleFilterManager",
  coordinator: "roleFilterCoordinator",
  staff: "roleFilterStaff",
  client: "roleFilterClient",
};

export function tUsers(key: UsersI18nKey): string {
  return userMessages[key];
}

/** Localised label for a JWT/API role value shown in tables and tags. */
export function userRoleDisplay(role: string): string {
  const key = roleLabelKeyByRole[role.toLowerCase()];
  return key ? tUsers(key) : role;
}

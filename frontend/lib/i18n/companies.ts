/**
 * Company pages i18n keys (pt-PT).
 *
 * All user-visible strings for the Company list, profile, and archive flow
 * go through this module. Keys are organised by page/feature.
 */

const companyMessages = {
  // ── Company List ──────────────────────────────────────────────────────
  listTitle: "Empresas",
  listSearchPlaceholder: "Pesquisar por nome ou NIF…",
  listFilterMaturityStage: "Estágio de maturidade",
  listFilterSector: "Setor (CAE)",
  listFilterActiveOnly: "Apenas ativas",
  listFilterAll: "Todas",
  listFilterActive: "Ativas",
  listFilterArchived: "Arquivadas",
  listColumnCompanyName: "Nome",
  listColumnNif: "NIF",
  listColumnSector: "Setor (CAE)",
  listColumnMaturityStage: "Estágio",
  listColumnEmployees: "Colaboradores",
  listColumnContractStatus: "Estado do contrato",
  listColumnActions: "Ações",
  listActionView: "Ver perfil",
  listActionEdit: "Editar",
  listActionArchive: "Arquivar",
  listArchiveConfirmTitle: "Arquivar empresa",
  listArchiveConfirmDescription:
    "Tem a certeza que pretende arquivar esta empresa? Esta ação pode ser revertida.",
  listArchiveSuccess: "Empresa arquivada com sucesso.",
  listArchiveError: "Erro ao arquivar a empresa.",
  listEmptyTitle: "Sem empresas",
  listEmptyDescription: "Não foram encontradas empresas com os filtros selecionados.",
  listRegisterButton: "Registar empresa",
  listShowingPagination: "A mostrar {from}–{to} de {total} empresas",
  listResultCount: "{count} empresa(s) encontrada(s)",

  // ── Maturity Stage Tags ──────────────────────────────────────────────
  stageIncubated: "Incubada",
  stageStartup: "Startup",
  stageIntermediate: "Intermédia",
  stageConsolidated: "Consolidada",

  // ── Contract Status Tags ──────────────────────────────────────────────
  contractActive: "Ativo",
  contractExpired: "Expirado",
  contractDraft: "Rascunho",

  // ── Archived Badge ───────────────────────────────────────────────────
  badgeArchived: "Arquivada",
} as const;

export type CompanyI18nKey = keyof typeof companyMessages;

export function tCompany(key: CompanyI18nKey): string {
  return companyMessages[key];
}

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
  listDirectoryTitle: "Diretório de empresas",
  listKpiTotal: "Total registado",
  listKpiActive: "Empresas ativas",
  listKpiArchived: "Arquivadas",
  listKpiVisible: "Visíveis nesta página",

  // ── Company Form / Detail ─────────────────────────────────────────────
  formCreateTitle: "Registar empresa",
  formEditTitle: "Editar empresa",
  formCreateSubmit: "Registar empresa",
  formUpdateSubmit: "Guardar alterações",
  formCreateSuccess: "Empresa registada com sucesso.",
  formUpdateSuccess: "Empresa atualizada com sucesso.",
  formSaveError: "Não foi possível guardar a empresa.",
  formBackToList: "Voltar à lista",
  formCancel: "Cancelar",
  formLoading: "A carregar empresa…",
  formFieldName: "Nome",
  formFieldNameRequired: "Indique o nome da empresa.",
  formFieldTaxId: "NIF",
  formFieldTaxIdRequired: "Indique o NIF.",
  formFieldLegalRepresentative: "Representante legal",
  formFieldLegalRepresentativeRequired: "Indique o representante legal.",
  formFieldEmail: "E-mail",
  formFieldEmailInvalid: "Indique um e-mail válido.",
  formFieldPhone: "Telefone",
  formFieldAddress: "Morada",
  formFieldDescription: "Descrição",
  formFieldCae: "Setor (CAE)",
  formFieldCaeRequired: "Selecione o setor CAE.",
  formFieldCaePlaceholder: "Selecione o setor",
  formFieldMaturityStage: "Estágio de maturidade",
  formFieldMaturityStageRequired: "Selecione o estágio de maturidade.",
  formFieldMaturityStagePlaceholder: "Selecione o estágio",
  detailBack: "Voltar ao perfil",
  detailNotFound: "Empresa não encontrada.",
  detailProfileTitle: "Perfil da empresa",
  detailEmployeesTitle: "Colaboradores",
  detailEmployeesEmpty: "Sem colaboradores ativos para apresentar.",
  detailEmployeeName: "Nome",
  detailEmployeeType: "Tipo",
  detailEmployeeStart: "Início",
  detailEmployeeEnd: "Fim",
  detailEmployeeStatus: "Estado",
  detailStatusActive: "Ativo",
  detailStatusInactive: "Inativo",
  detailDocumentsTitle: "Documentos",

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

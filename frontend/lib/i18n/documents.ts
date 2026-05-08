const documentMessages = {
  uploadButton: "Carregar documento",
  uploadSuccess: "Documento carregado com sucesso.",
  uploadErrorGeneric: "Não foi possível carregar o documento.",
  uploadErrorMime: "Tipo de ficheiro não suportado.",
  uploadErrorTooLarge: "O ficheiro excede o tamanho máximo permitido ({maxSize}).",
  listTitle: "Documentos",
  listEmpty: "Sem documentos.",
  listLoadError: "Não foi possível carregar os documentos.",
  colName: "Nome",
  colSize: "Tamanho",
  colDescription: "Descrição",
  colUploadedAt: "Data",
  colActions: "Ações",
  valueEmpty: "—",
  actionDownload: "Descarregar",
  actionDelete: "Eliminar",
  deleteConfirm: "Eliminar este documento?",
  deleteOk: "Eliminar",
  deleteCancel: "Cancelar",
  deleteSuccess: "Documento eliminado.",
  deleteError: "Não foi possível eliminar o documento.",
  downloadError: "Não foi possível descarregar o documento.",
} as const;

export type DocumentsI18nKey = keyof typeof documentMessages;

export function tDocuments(key: DocumentsI18nKey): string {
  return documentMessages[key];
}

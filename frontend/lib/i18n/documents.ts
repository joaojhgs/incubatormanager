const documentMessages = {
  uploadButton: "Carregar documento",
  uploadSuccess: "Documento carregado com sucesso.",
  uploadErrorGeneric: "Não foi possível carregar o documento.",
  uploadErrorMime: "Tipo de ficheiro não suportado.",
  uploadErrorTooLarge: "O ficheiro excede o tamanho máximo permitido ({maxSize}).",
} as const;

export type DocumentsI18nKey = keyof typeof documentMessages;

export function tDocuments(key: DocumentsI18nKey): string {
  return documentMessages[key];
}

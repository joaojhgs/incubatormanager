export interface AuthUser {
  id: string;
  email?: string;
  role: string;
  companyId?: string | null;
}

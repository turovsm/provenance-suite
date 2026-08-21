export type UserRole = 'guest' | 'user' | 'trusted' | 'moderator' | 'admin';

export const ROLE_LEVELS: Record<UserRole, number> = {
  guest: 0,
  user: 1,
  trusted: 2,
  moderator: 3,
  admin: 4,
};

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

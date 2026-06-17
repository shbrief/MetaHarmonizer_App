/* ------------------------------------------------------------------ */
/*  Auth, sessions, API tokens, and admin endpoints                    */
/* ------------------------------------------------------------------ */

import { apiFetch, setAccessToken } from './http';
import type {
    ApiTokenCreated,
    ApiTokenInfo,
    Role,
    SessionInfo,
    TokenResponse,
    User,
} from './types';

/* ---------- Auth ---------- */

export async function register(input: {
    email: string;
    password: string;
    name?: string;
}): Promise<TokenResponse> {
    const res = await apiFetch<TokenResponse>('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
        skipAuthRetry: true,
    });
    setAccessToken(res.access_token);
    return res;
}

export async function login(input: { email: string; password: string }): Promise<TokenResponse> {
    const res = await apiFetch<TokenResponse>('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
        skipAuthRetry: true,
    });
    setAccessToken(res.access_token);
    return res;
}

/** Attempt to restore a session from the refresh cookie (called on app boot). */
export async function bootstrapSession(): Promise<User | null> {
    try {
        const res = await apiFetch<TokenResponse>('/auth/refresh', {
            method: 'POST',
            skipAuthRetry: true,
        });
        setAccessToken(res.access_token);
        return res.user;
    } catch {
        setAccessToken(null);
        return null;
    }
}

export async function getMe(): Promise<User> {
    return apiFetch<User>('/auth/me');
}

export async function logout(): Promise<void> {
    try {
        await apiFetch('/auth/logout', { method: 'POST', json: false });
    } finally {
        setAccessToken(null);
    }
}

/* ---------- Sessions ---------- */

export async function listSessions(): Promise<SessionInfo[]> {
    return apiFetch<SessionInfo[]>('/auth/sessions');
}

export async function revokeSession(id: number): Promise<void> {
    await apiFetch(`/auth/sessions/${id}`, { method: 'DELETE', json: false });
}

/* ---------- API tokens ---------- */

export async function listApiTokens(): Promise<ApiTokenInfo[]> {
    return apiFetch<ApiTokenInfo[]>('/tokens');
}

export async function createApiToken(scope: 'read' | 'write'): Promise<ApiTokenCreated> {
    return apiFetch<ApiTokenCreated>('/tokens', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scope }),
    });
}

export async function revokeApiToken(id: number): Promise<void> {
    await apiFetch(`/tokens/${id}`, { method: 'DELETE', json: false });
}

/* ---------- Admin ---------- */

export async function adminListUsers(): Promise<User[]> {
    return apiFetch<User[]>('/admin/users');
}

export async function adminSetRole(userId: number, role: Role): Promise<User> {
    return apiFetch<User>(`/admin/users/${userId}/role`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role }),
    });
}

export async function adminSetActive(userId: number, isActive: boolean): Promise<User> {
    return apiFetch<User>(`/admin/users/${userId}/active`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: isActive }),
    });
}

export async function adminForceLogout(userId: number): Promise<void> {
    await apiFetch(`/admin/users/${userId}/logout`, { method: 'POST', json: false });
}

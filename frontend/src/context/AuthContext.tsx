import {
    createContext,
    useContext,
    useEffect,
    useMemo,
    useState,
    type ReactNode,
} from 'react';
import {
    bootstrapSession,
    login as apiLogin,
    logout as apiLogout,
    register as apiRegister,
} from '../api/auth';
import type { Role, User } from '../api/types';

interface AuthContextValue {
    user: User | null;
    /** True until the initial refresh-on-boot resolves. */
    initializing: boolean;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<User>;
    /**
     * Create an account. Does NOT sign in — non-bootstrap users must verify
     * their email first. Resolves to the server's next-step message.
     */
    register: (
        email: string,
        password: string,
        name?: string,
        requestAdmin?: boolean,
    ) => Promise<string>;
    logout: () => Promise<void>;
    setUser: (u: User | null) => void;
    /** Role hierarchy check: curator < admin. */
    hasRole: (minimum: Role) => boolean;
}

const ROLE_RANK: Record<Role, number> = { curator: 1, admin: 2 };

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [initializing, setInitializing] = useState(true);

    // On boot, try to restore a session from the httpOnly refresh cookie.
    useEffect(() => {
        let active = true;
        bootstrapSession()
            .then((u) => {
                if (active) setUser(u);
            })
            .finally(() => {
                if (active) setInitializing(false);
            });
        return () => {
            active = false;
        };
    }, []);

    const value = useMemo<AuthContextValue>(
        () => ({
            user,
            initializing,
            isAuthenticated: !!user,
            setUser,
            hasRole: (minimum) => !!user && ROLE_RANK[user.role] >= ROLE_RANK[minimum],
            login: async (email, password) => {
                const res = await apiLogin({ email, password });
                setUser(res.user);
                return res.user;
            },
            register: async (email, password, name, requestAdmin) => {
                const res = await apiRegister({
                    email,
                    password,
                    name,
                    request_admin: requestAdmin,
                });
                return res.message;
            },
            logout: async () => {
                await apiLogout();
                setUser(null);
            },
        }),
        [user, initializing],
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within <AuthProvider>');
    return ctx;
}

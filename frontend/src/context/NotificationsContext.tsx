/* ------------------------------------------------------------------ */
/*  Per-user in-app notifications (bell icon)                          */
/* ------------------------------------------------------------------ */
/*
 * A lightweight, per-user notification centre. Notifications are raised by
 * other parts of the app (e.g. JobsContext when a harmonization finishes) via
 * `notify()`, surfaced as an unread badge on the header bell, and persisted to
 * localStorage so they survive a reload. Storage is namespaced per user id so
 * two accounts sharing a browser never see each other's notifications.
 *
 * Desktop notifications are strictly opt-in: nothing is shown until the user
 * enables them (which triggers the browser permission prompt). The preference
 * is remembered per user.
 */

import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useRef,
    useState,
    type ReactNode,
} from 'react';
import { useAuth } from './AuthContext';

export type NotificationKind = 'job_done' | 'job_failed' | 'job_cancelled' | 'info';

export interface AppNotification {
    id: string;
    kind: NotificationKind;
    title: string;
    body: string;
    /** Optional in-app link target (e.g. `/review/<studyId>`). */
    href?: string;
    createdAt: number;
    read: boolean;
}

interface NotificationsContextValue {
    notifications: AppNotification[];
    unreadCount: number;
    /** Raise a new notification (also fires a desktop notification if enabled). */
    notify(input: Omit<AppNotification, 'id' | 'createdAt' | 'read'>): void;
    markAllRead(): void;
    dismiss(id: string): void;
    clear(): void;
    /** Whether opt-in desktop notifications are currently active. */
    desktopEnabled: boolean;
    /** Request desktop-notification permission and enable them. */
    enableDesktop(): Promise<void>;
    /** Turn desktop notifications back off (permission is not revoked). */
    disableDesktop(): void;
}

const NotificationsContext = createContext<NotificationsContextValue | null>(null);

const STORAGE_PREFIX = 'mh.notifs.v1';
const DESKTOP_PREF_PREFIX = 'mh.notifs.desktop.v1';
const storageKey = (userId: number | null | undefined): string | null =>
    userId == null ? null : `${STORAGE_PREFIX}.${userId}`;
const desktopPrefKey = (userId: number | null | undefined): string | null =>
    userId == null ? null : `${DESKTOP_PREF_PREFIX}.${userId}`;

/** Cap stored notifications so the list (and localStorage) stays bounded. */
const MAX_NOTIFICATIONS = 50;

function loadPersisted(key: string | null): AppNotification[] {
    if (!key) return [];
    try {
        const raw = localStorage.getItem(key);
        if (!raw) return [];
        const parsed = JSON.parse(raw) as AppNotification[];
        return Array.isArray(parsed) ? parsed.slice(0, MAX_NOTIFICATIONS) : [];
    } catch {
        return [];
    }
}

function loadDesktopPref(key: string | null): boolean {
    if (!key) return false;
    try {
        // The toggle is only truly "on" when the user opted in *and* the browser
        // permission is still granted. The permission can drift out of sync with
        // the stored pref (e.g. it was reset to "ask", or site data was cleared),
        // so reconcile here — otherwise the toggle shows "on" while popups
        // silently never fire.
        if (localStorage.getItem(key) !== '1') return false;
        return supportsDesktop() && Notification.permission === 'granted';
    } catch {
        return false;
    }
}

const supportsDesktop = (): boolean =>
    typeof window !== 'undefined' && 'Notification' in window;

const makeId = (): string =>
    typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

export function NotificationsProvider({ children }: { children: ReactNode }) {
    const { user } = useAuth();
    const userId = user?.id ?? null;

    const [notifications, setNotifications] = useState<AppNotification[]>(() =>
        loadPersisted(storageKey(userId)),
    );
    const [desktopEnabled, setDesktopEnabled] = useState<boolean>(() =>
        loadDesktopPref(desktopPrefKey(userId)),
    );
    // A ref the notify() callback reads so it isn't recreated on every change.
    const desktopRef = useRef(desktopEnabled);
    desktopRef.current = desktopEnabled;

    // Swap to the signed-in user's own notifications + preference on login /
    // logout / account switch within the same browser.
    const lastUserId = useRef<number | null>(userId);
    useEffect(() => {
        if (lastUserId.current === userId) return;
        lastUserId.current = userId;
        setNotifications(loadPersisted(storageKey(userId)));
        setDesktopEnabled(loadDesktopPref(desktopPrefKey(userId)));
    }, [userId]);

    // Persist notifications under the current user's key (nothing when logged out).
    useEffect(() => {
        const key = storageKey(userId);
        if (!key) return;
        try {
            localStorage.setItem(key, JSON.stringify(notifications.slice(0, MAX_NOTIFICATIONS)));
        } catch {
            /* storage full / disabled — non-fatal */
        }
    }, [notifications, userId]);

    const notify = useCallback<NotificationsContextValue['notify']>((input) => {
        const entry: AppNotification = {
            ...input,
            id: makeId(),
            createdAt: Date.now(),
            read: false,
        };
        setNotifications((prev) => [entry, ...prev].slice(0, MAX_NOTIFICATIONS));

        // Mirror to the OS only when the user opted in and granted permission.
        if (
            desktopRef.current &&
            supportsDesktop() &&
            Notification.permission === 'granted'
        ) {
            try {
                const n = new Notification(input.title, {
                    body: input.body,
                    tag: entry.id,
                });
                if (input.href) {
                    n.onclick = () => {
                        window.focus();
                        window.location.assign(input.href!);
                    };
                }
            } catch {
                /* Some browsers throw if called outside a user gesture — ignore. */
            }
        }
    }, []);

    const markAllRead = useCallback(() => {
        setNotifications((prev) =>
            prev.some((n) => !n.read) ? prev.map((n) => ({ ...n, read: true })) : prev,
        );
    }, []);

    const dismiss = useCallback((id: string) => {
        setNotifications((prev) => prev.filter((n) => n.id !== id));
    }, []);

    const clear = useCallback(() => setNotifications([]), []);

    const enableDesktop = useCallback(async () => {
        if (!supportsDesktop()) return;
        let permission = Notification.permission;
        if (permission === 'default') {
            permission = await Notification.requestPermission();
        }
        if (permission === 'granted') {
            setDesktopEnabled(true);
            const key = desktopPrefKey(lastUserId.current);
            if (key) {
                try {
                    localStorage.setItem(key, '1');
                } catch {
                    /* non-fatal */
                }
            }
        }
    }, []);

    const disableDesktop = useCallback(() => {
        setDesktopEnabled(false);
        const key = desktopPrefKey(lastUserId.current);
        if (key) {
            try {
                localStorage.removeItem(key);
            } catch {
                /* non-fatal */
            }
        }
    }, []);

    const value = useMemo<NotificationsContextValue>(
        () => ({
            notifications,
            unreadCount: notifications.reduce((n, x) => n + (x.read ? 0 : 1), 0),
            notify,
            markAllRead,
            dismiss,
            clear,
            desktopEnabled,
            enableDesktop,
            disableDesktop,
        }),
        [notifications, notify, markAllRead, dismiss, clear, desktopEnabled, enableDesktop, disableDesktop],
    );

    return (
        <NotificationsContext.Provider value={value}>{children}</NotificationsContext.Provider>
    );
}

export function useNotifications(): NotificationsContextValue {
    const ctx = useContext(NotificationsContext);
    if (!ctx) throw new Error('useNotifications must be used within <NotificationsProvider>');
    return ctx;
}

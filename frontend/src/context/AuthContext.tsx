import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserPrincipal } from '../types';
import { api, getAuthToken } from '../api/client';

interface AuthContextType {
  user: UserPrincipal | null;
  isAuthenticated: boolean;
  role: string;
  loginDemo: (role: string) => Promise<void>;
  logout: () => Promise<void>;
  loading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserPrincipal | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Auto-login into demo mode with operator role on startup for local convenience
    const initAuth = async () => {
      try {
        const res = await api.loginDemo('demo-operator', 'operator');
        setUser(res.user);
      } catch (err: unknown) {
        // Fallback: demo mode not active or requires manual login
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    initAuth();
  }, []);

  const loginDemo = async (selectedRole: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.loginDemo(`demo-${selectedRole}`, selectedRole);
      setUser(res.user);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Login failed';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await api.logout();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const primaryRole = user?.roles?.[0] || 'viewer';

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user && !!getAuthToken(),
        role: primaryRole,
        loginDemo,
        logout,
        loading,
        error
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

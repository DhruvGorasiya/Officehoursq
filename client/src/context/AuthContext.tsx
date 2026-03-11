"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useRealtimeChannel } from "@/hooks/useRealtimeChannel";

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'student' | 'ta' | 'professor';
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  unreadCount: number;
  login: (token: string, user: User) => void;
  logout: () => void;
  revalidate: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
   const [unreadCount, setUnreadCount] = useState(0);
  const router = useRouter();

  useEffect(() => {
    // Check for stored token and fetch user on mount
    const storedToken = localStorage.getItem("token");
    if (storedToken) {
      setToken(storedToken);
      fetchUser(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async (authToken: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/auth/me`, {
        headers: {
          "Authorization": `Bearer ${authToken}`
        }
      });
      const data = await response.json();
      if (data.success && data.data) {
        setUser(data.data as User);
      } else {
        // Token might be invalid or expired
        localStorage.removeItem("token");
        setToken(null);
      }
    } catch (error) {
      console.error("Error fetching user:", error);
      localStorage.removeItem("token");
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = (authToken: string, userData: User) => {
    localStorage.setItem("token", authToken);
    setToken(authToken);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
    setUnreadCount(0);
    router.push("/login");
  };

  const revalidate = async () => {
    if (token) {
      await fetchUser(token);
    }
  };

  // Realtime: subscribe to user-specific notification channel when logged in
  useRealtimeChannel(
    user ? `user:${user.id}` : null,
    {
      onNotificationEvent: () => {
        setUnreadCount((prev) => prev + 1);
      },
    }
  );

  return (
    <AuthContext.Provider value={{ user, token, loading, unreadCount, login, logout, revalidate }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Bell } from "lucide-react";

interface NavBarProps {
  title?: string;
  statusBadge?: "active" | "scheduled" | null;
}

export default function NavBar({ title = "OfficeHoursQ", statusBadge = null }: NavBarProps) {
  const { user, logout, unreadCount } = useAuth();
  
  const getInitials = (name: string) => {
    return name.split(" ").map((n) => n[0]).join("").substring(0, 2).toUpperCase();
  };

  return (
    <nav className="flex items-center justify-between w-full h-16 px-6 bg-surface border-b border-border">
      <div className="flex items-center gap-4">
        {/* Placeholder for Back Arrow - rendering conditionally based on app state could be added here */}
        <Link href="/dashboard" className="text-xl font-bold text-text-primary hover:text-accent transition-colors">
          {title}
        </Link>
        
        {statusBadge === "active" && (
          <div className="flex items-center gap-2 px-3 py-1 bg-green/10 text-green rounded-badge text-sm font-medium">
            <span className="w-2 h-2 rounded-full bg-green" />
            Active
          </div>
        )}
        {statusBadge === "scheduled" && (
          <div className="flex items-center gap-2 px-3 py-1 bg-amber/10 text-amber rounded-badge text-sm font-medium">
            <span className="w-2 h-2 rounded-full bg-amber" />
            Scheduled
          </div>
        )}
      </div>

      <div className="flex items-center gap-6">
        <button className="relative text-text-secondary hover:text-text-primary transition-colors">
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-4 min-w-4 px-1 items-center justify-center rounded-badge bg-red text-[10px] font-bold text-white">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </button>

        {user ? (
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-accent text-white font-bold text-sm select-none">
              {getInitials(user.name)}
            </div>
            <button 
              onClick={logout}
              className="text-sm text-text-muted hover:text-text-primary transition-colors"
            >
              Log out
            </button>
          </div>
        ) : (
          <Link href="/login" className="text-sm font-medium text-accent hover:text-white transition-colors">
            Sign In
          </Link>
        )}
      </div>
    </nav>
  );
}

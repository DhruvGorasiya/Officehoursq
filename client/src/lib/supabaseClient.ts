"use client";

import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL as string | undefined;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string | undefined;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  // In dev environments without Supabase configured, we still want the app to run.
  // The realtime hooks will effectively be no-ops when the client is undefined.
  // eslint-disable-next-line no-console
  console.warn("Supabase env vars are not configured; realtime features will be disabled.");
}

export const supabaseClient =
  SUPABASE_URL && SUPABASE_ANON_KEY
    ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
    : null;


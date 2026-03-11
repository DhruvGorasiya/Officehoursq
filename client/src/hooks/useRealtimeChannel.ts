"use client";

import { useEffect } from "react";
import { supabaseClient } from "@/lib/supabaseClient";

type QuestionEventHandler = (payload: any) => void;
type SessionEventHandler = (payload: any) => void;
type NotificationEventHandler = (payload: any) => void;

interface RealtimeHandlers {
  onQuestionEvent?: QuestionEventHandler;
  onSessionEvent?: SessionEventHandler;
  onNotificationEvent?: NotificationEventHandler;
}

export function useRealtimeChannel(channelName: string | null, handlers: RealtimeHandlers) {
  useEffect(() => {
    if (!channelName || !supabaseClient) return;

    const channel = supabaseClient.channel(channelName);

    if (handlers.onQuestionEvent) {
      channel.on(
        "broadcast",
        { event: "question:submitted" },
        (payload) => handlers.onQuestionEvent?.(payload.payload)
      );
      channel.on(
        "broadcast",
        { event: "question:claimed" },
        (payload) => handlers.onQuestionEvent?.(payload.payload)
      );
      channel.on(
        "broadcast",
        { event: "question:resolved" },
        (payload) => handlers.onQuestionEvent?.(payload.payload)
      );
      channel.on(
        "broadcast",
        { event: "question:deferred" },
        (payload) => handlers.onQuestionEvent?.(payload.payload)
      );
      channel.on(
        "broadcast",
        { event: "question:withdrawn" },
        (payload) => handlers.onQuestionEvent?.(payload.payload)
      );
    }

    if (handlers.onSessionEvent) {
      channel.on(
        "broadcast",
        { event: "session:updated" },
        (payload) => handlers.onSessionEvent?.(payload.payload)
      );
    }

    if (handlers.onNotificationEvent) {
      channel.on(
        "broadcast",
        { event: "notification:new" },
        (payload) => handlers.onNotificationEvent?.(payload.payload)
      );
    }

    channel.subscribe();

    return () => {
      channel.unsubscribe();
    };
  }, [channelName, handlers.onQuestionEvent, handlers.onSessionEvent, handlers.onNotificationEvent]);
}


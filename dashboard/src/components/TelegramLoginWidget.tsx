import React, { useEffect, useRef } from "react";

interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
}

interface TelegramLoginWidgetProps {
  botName: string;
  onAuth: (user: TelegramUser) => void;
  buttonSize?: "large" | "medium" | "small";
  cornerRadius?: number;
  requestAccess?: "write";
}

export default function TelegramLoginWidget({
  botName,
  onAuth,
  buttonSize = "large",
  cornerRadius = 14,
  requestAccess = "write",
}: TelegramLoginWidgetProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Expose the callback to the window object so the script can find it
    (window as any).onTelegramAuth = (user: TelegramUser) => {
      onAuth(user);
    };

    if (containerRef.current) {
      // Clear previous script if any
      containerRef.current.innerHTML = "";
      
      const script = document.createElement("script");
      script.src = "https://telegram.org/js/telegram-widget.js?23";
      script.async = true;
      script.setAttribute("data-telegram-login", botName);
      script.setAttribute("data-size", buttonSize);
      script.setAttribute("data-radius", cornerRadius.toString());
      if (requestAccess) {
        script.setAttribute("data-request-access", requestAccess);
      }
      script.setAttribute("data-onauth", "onTelegramAuth(user)");
      
      containerRef.current.appendChild(script);
    }

    return () => {
      // Cleanup global callback
      delete (window as any).onTelegramAuth;
    };
  }, [botName, buttonSize, cornerRadius, requestAccess, onAuth]);

  return <div ref={containerRef} className="flex justify-center" />;
}

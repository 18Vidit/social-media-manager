"use client";

import { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import DashboardPage from "@/components/pages/DashboardPage";
import ContentStudioPage from "@/components/pages/ContentStudioPage";
import CommentsPage from "@/components/pages/CommentsPage";
import SchedulePage from "@/components/pages/SchedulePage";
import AnalyticsPage from "@/components/pages/AnalyticsPage";
import BrandVoicePage from "@/components/pages/BrandVoicePage";
import PipelineTracePage from "@/components/pages/PipelineTracePage";
import ToastContainer from "@/components/ui/ToastContainer";

export type PageId = "dashboard" | "content" | "comments" | "schedule" | "analytics" | "brand" | "pipeline";

export interface Toast {
  id: string;
  type: "success" | "error" | "info";
  message: string;
}

export default function Home() {
  const [activePage, setActivePage] = useState<PageId>("dashboard");
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [backendStatus, setBackendStatus] = useState<"connecting" | "connected" | "offline">("connecting");
  const [brandId, setBrandId] = useState<string>("demo-brand-001");

  const addToast = useCallback((type: Toast["type"], message: string) => {
    const id = Date.now().toString();
    setToasts(prev => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  // Check backend status on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await fetch("http://localhost:8000/health");
        if (res.ok) {
          setBackendStatus("connected");
        } else {
          setBackendStatus("offline");
        }
      } catch {
        setBackendStatus("offline");
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  const renderPage = () => {
    const props = { brandId, addToast, backendStatus };
    switch (activePage) {
      case "dashboard": return <DashboardPage {...props} />;
      case "content": return <ContentStudioPage {...props} />;
      case "comments": return <CommentsPage {...props} />;
      case "schedule": return <SchedulePage {...props} />;
      case "analytics": return <AnalyticsPage {...props} />;
      case "brand": return <BrandVoicePage {...props} />;
      case "pipeline": return <PipelineTracePage {...props} />;
      default: return <DashboardPage {...props} />;
    }
  };

  return (
    <div className="app-layout">
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
        backendStatus={backendStatus}
      />
      <main className="main-content">
        {renderPage()}
      </main>
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
}

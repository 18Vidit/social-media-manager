"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  brandId: string;
  onConnected?: (account: any) => void;
  addToast: (type: "success" | "error" | "info", message: string) => void;
}

export default function InstagramConnectModal({
  isOpen,
  onClose,
  brandId,
  onConnected,
  addToast,
}: Props) {
  const [activeTab, setActiveTab] = useState<"connect" | "guide">("connect");
  const [token, setToken] = useState("");
  const [accountId, setAccountId] = useState("");
  const [autoSync, setAutoSync] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [status, setStatus] = useState<any>(null);
  const [loadingStatus, setLoadingStatus] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadStatus();
    }
  }, [isOpen, brandId]);

  const loadStatus = async () => {
    setLoadingStatus(true);
    try {
      const data = await api.getInstagramStatus(brandId);
      setStatus(data);
    } catch {
      setStatus({ connected: false });
    }
    setLoadingStatus(false);
  };

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) {
      addToast("error", "Please provide a valid Meta/Instagram Access Token.");
      return;
    }

    setConnecting(true);
    try {
      const res = await api.connectInstagram({
        brand_id: brandId,
        access_token: token.trim(),
        account_id: accountId.trim() || undefined,
        auto_sync: autoSync,
      });

      addToast("success", `Successfully connected to Instagram as @${res.account.username}!`);
      if (res.posts_synced) {
        addToast("info", `Synced ${res.posts_synced} posts and ${res.comments_synced || 0} comments.`);
      }
      setToken("");
      await loadStatus();
      if (onConnected) onConnected(res.account);
    } catch (err: any) {
      addToast("error", err.message || "Failed to connect to Instagram.");
    }
    setConnecting(false);
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      addToast("info", "Syncing latest posts and comments from Instagram...");
      const res = await api.syncInstagram(brandId, 25);
      addToast("success", `Synced ${res.posts_synced || res.total_posts_processed || 0} posts & ${res.comments_synced || 0} comments! Voice profile calibrated.`);
      await loadStatus();
      if (onConnected) onConnected(status);
    } catch (err: any) {
      addToast("error", `Sync failed: ${err.message}`);
    }
    setSyncing(false);
  };

  const handleDisconnect = async () => {
    if (!confirm("Are you sure you want to disconnect this Instagram account?")) return;
    try {
      await api.disconnectInstagram(brandId);
      addToast("info", "Instagram account disconnected.");
      await loadStatus();
    } catch (err: any) {
      addToast("error", `Disconnect failed: ${err.message}`);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
        padding: 20,
      }}
      onClick={onClose}
    >
      <div
        className="card glass"
        style={{
          width: "100%",
          maxWidth: 620,
          maxHeight: "90vh",
          overflowY: "auto",
          background: "rgba(15, 23, 42, 0.95)",
          border: "1px solid rgba(255, 255, 255, 0.15)",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 30px rgba(225, 48, 108, 0.2)",
          position: "relative",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 12,
                background: "linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                fontWeight: 900,
                fontSize: "1.2rem",
                boxShadow: "0 4px 15px rgba(225, 48, 108, 0.4)",
              }}
            >
              IG
            </div>
            <div>
              <h2 style={{ fontSize: "1.25rem", margin: 0 }}>Instagram Integration</h2>
              <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                Connect your real account to replace demo data with live posts & comments
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="btn btn-secondary btn-sm"
            style={{ padding: "4px 10px", fontSize: "1rem" }}
          >
            ✕
          </button>
        </div>

        {/* Tab Controls */}
        <div style={{ display: "flex", gap: 8, marginBottom: 20, borderBottom: "1px solid var(--border-color)", paddingBottom: 12 }}>
          <button
            className={`btn btn-sm ${activeTab === "connect" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setActiveTab("connect")}
            style={{ borderRadius: 8 }}
          >
            Account & Connection
          </button>
          <button
            className={`btn btn-sm ${activeTab === "guide" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setActiveTab("guide")}
            style={{ borderRadius: 8 }}
          >
            Setup Guide (60s)
          </button>
        </div>

        {activeTab === "connect" ? (
          <div>
            {/* If Already Connected */}
            {status?.connected ? (
              <div
                style={{
                  background: "rgba(16, 185, 129, 0.08)",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  borderRadius: "var(--radius-md)",
                  padding: 16,
                  marginBottom: 20,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                  {status.profile_picture_url ? (
                    <img
                      src={status.profile_picture_url}
                      alt={status.username}
                      style={{ width: 56, height: 56, borderRadius: "50%", objectFit: "cover", border: "2px solid #10b981" }}
                    />
                  ) : (
                    <div
                      style={{
                        width: 56,
                        height: 56,
                        borderRadius: "50%",
                        background: "var(--gradient-primary)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "1.5rem",
                        fontWeight: "bold",
                      }}
                    >
                      {(status.name || status.username || "I")[0]}
                    </div>
                  )}
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontWeight: 700, fontSize: "1.1rem" }}>{status.name || status.username}</span>
                      <span className="badge badge-success">Connected</span>
                    </div>
                    <div style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginTop: 2 }}>
                      @{status.username} • {status.followers_count?.toLocaleString()} followers
                    </div>
                    {status.biography && (
                      <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: "6px 0 0 0", maxHeight: 40, overflow: "hidden" }}>
                        {status.biography}
                      </p>
                    )}
                  </div>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(3, 1fr)",
                    gap: 8,
                    marginTop: 16,
                    paddingTop: 12,
                    borderTop: "1px solid rgba(255,255,255,0.08)",
                  }}
                >
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Synced Posts</div>
                    <div style={{ fontWeight: 700, fontSize: "1.1rem", color: "var(--accent-cyan)" }}>
                      {status.synced_posts_count || 0}
                    </div>
                  </div>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Live Comments</div>
                    <div style={{ fontWeight: 700, fontSize: "1.1rem", color: "var(--accent-purple)" }}>
                      {status.synced_comments_count || 0}
                    </div>
                  </div>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Last Sync</div>
                    <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                      {status.last_synced_at ? new Date(status.last_synced_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "Just now"}
                    </div>
                  </div>
                </div>

                <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
                  <button
                    className="btn btn-primary"
                    style={{ flex: 1 }}
                    onClick={handleSync}
                    disabled={syncing}
                  >
                    {syncing ? "Syncing Feed..." : "↻ Sync Live Data Now"}
                  </button>
                  <button
                    className="btn btn-secondary"
                    style={{ borderColor: "rgba(239, 68, 68, 0.4)", color: "var(--accent-red)" }}
                    onClick={handleDisconnect}
                  >
                    Disconnect
                  </button>
                </div>
              </div>
            ) : null}

            {/* Connection Form */}
            <form onSubmit={handleConnect}>
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: 6 }}>
                  Meta / Instagram Graph API Access Token <span style={{ color: "var(--accent-red)" }}>*</span>
                </label>
                <input
                  type="password"
                  className="input"
                  style={{ width: "100%", fontFamily: "monospace", fontSize: "0.85rem" }}
                  placeholder="EAA... (Paste User or Page Token from Meta Developer Portal)"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  required
                />
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 4 }}>
                  Supports Meta User Token, Page Access Token, or Long-Lived Token.
                </div>
              </div>

              <div style={{ marginBottom: 16 }}>
                <label style={{ display: "block", fontSize: "0.875rem", fontWeight: 600, marginBottom: 6 }}>
                  Instagram Business Account ID <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>(Optional - auto-discovered if left blank)</span>
                </label>
                <input
                  type="text"
                  className="input"
                  style={{ width: "100%" }}
                  placeholder="e.g. 17841400000000000"
                  value={accountId}
                  onChange={(e) => setAccountId(e.target.value)}
                />
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 20 }}>
                <input
                  type="checkbox"
                  id="autoSync"
                  checked={autoSync}
                  onChange={(e) => setAutoSync(e.target.checked)}
                  style={{ accentColor: "var(--accent-primary)", width: 16, height: 16 }}
                />
                <label htmlFor="autoSync" style={{ fontSize: "0.85rem", cursor: "pointer" }}>
                  Automatically import recent posts & audience comments immediately upon connection
                </label>
              </div>

              <div style={{ display: "flex", gap: 10 }}>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{
                    flex: 1,
                    background: "linear-gradient(135deg, #e1306c, #833ab4)",
                    border: "none",
                  }}
                  disabled={connecting}
                >
                  {connecting ? "Connecting to Meta..." : status?.connected ? "Update Connection / Re-authenticate" : "Connect Instagram Account"}
                </button>
              </div>
            </form>
          </div>
        ) : (
          <div style={{ fontSize: "0.875rem", lineHeight: 1.6 }}>
            <h4 style={{ margin: "0 0 12px 0", color: "var(--accent-cyan)" }}>
              How to get an Instagram Graph API Token in 60 Seconds:
            </h4>
            <ol style={{ paddingLeft: 20, margin: 0, display: "flex", flexDirection: "column", gap: 10 }}>
              <li>
                Visit the{" "}
                <a
                  href="https://developers.facebook.com/tools/explorer/"
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: "var(--accent-primary)", textDecoration: "underline" }}
                >
                  Meta Graph API Explorer ↗
                </a>
              </li>
              <li>Select your Meta App in the top right (or click <strong>Create App</strong>).</li>
              <li>
                In the <strong>Permissions</strong> dropdown, add these required scopes:
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, margin: "6px 0" }}>
                  {["instagram_basic", "pages_show_list", "pages_read_engagement", "instagram_manage_comments", "instagram_content_publish"].map((p) => (
                    <span key={p} className="badge badge-purple" style={{ fontFamily: "monospace", fontSize: "0.75rem" }}>
                      {p}
                    </span>
                  ))}
                </div>
              </li>
              <li>Click <strong>Generate Access Token</strong> and log in with your Instagram-connected Facebook account.</li>
              <li>Copy the generated token and paste it into the <strong>Account & Connection</strong> tab!</li>
            </ol>

            <div style={{ marginTop: 18, padding: 12, background: "rgba(0, 212, 255, 0.08)", borderRadius: "var(--radius-sm)", border: "1px solid rgba(0, 212, 255, 0.2)" }}>
              <div style={{ fontWeight: 600, color: "var(--accent-cyan)", marginBottom: 4 }}>
                💡 Pro Tip for Professional / Creator Accounts
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                Make sure your Instagram account is switched to a <strong>Professional / Creator</strong> account and connected to any Facebook Page (even an unpublished one). This enables full insights, comment moderation, and auto-publishing!
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

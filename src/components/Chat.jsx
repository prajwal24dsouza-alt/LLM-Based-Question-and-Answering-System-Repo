import { useEffect, useRef, useState } from "react";
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
});

function ChatMessage({ role, content }) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-[24px] px-4 py-3 text-sm leading-6 shadow-lg sm:max-w-[75%] ${
          isUser
            ? "rounded-br-md bg-gradient-to-r from-sky to-glow text-slate-950"
            : "rounded-bl-md border border-white/10 bg-white/[0.08] text-slate-100"
        }`}
      >
        <p className="mb-1 text-[11px] font-semibold uppercase tracking-[0.22em] opacity-75">
          {isUser ? "You" : "AI"}
        </p>
        <p className="whitespace-pre-wrap">{content}</p>
      </div>
    </div>
  );
}

function Chat({ hasDocument, activeDocument }) {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Upload a document to start. Once the PDF is indexed, ask a question and I’ll answer using the retrieved context.",
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const sendMessage = async () => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery || isLoading) {
      return;
    }

    if (!hasDocument) {
      setError("Upload and index a PDF before sending questions.");
      return;
    }

    const nextMessages = [...messages, { role: "user", content: trimmedQuery }];
    setMessages(nextMessages);
    setQuery("");
    setError("");
    setIsLoading(true);

    try {
      const response = await api.post("/ask", { query: trimmedQuery });
      setMessages([
        ...nextMessages,
        {
          role: "assistant",
          content: response.data.answer || "No answer was returned by the API.",
        },
      ]);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "The question could not be processed.");
      setMessages(nextMessages);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="flex min-h-[640px] flex-col rounded-[28px] border border-white/10 bg-panel/75 shadow-halo backdrop-blur">
      <div className="border-b border-white/10 px-5 py-5 sm:px-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-glow">Q&A Chat</p>
            <h2 className="mt-2 font-display text-2xl text-white">Ask grounded questions</h2>
          </div>
          <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs text-mist">
            {activeDocument ? `Indexed: ${activeDocument}` : "No document indexed yet"}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-5 sm:px-6">
        <div className="space-y-4">
          {messages.map((message, index) => (
            <ChatMessage
              key={`${message.role}-${index}`}
              role={message.role}
              content={message.content}
            />
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="rounded-[24px] rounded-bl-md border border-white/10 bg-white/[0.08] px-4 py-4 text-slate-100">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 animate-bounce rounded-full bg-glow [animation-delay:-0.3s]" />
                  <span className="h-2.5 w-2.5 animate-bounce rounded-full bg-sky [animation-delay:-0.15s]" />
                  <span className="h-2.5 w-2.5 animate-bounce rounded-full bg-ember" />
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      <div className="border-t border-white/10 px-5 py-5 sm:px-6">
        {error && (
          <div className="mb-4 rounded-2xl border border-rose-400/25 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-3 md:flex-row">
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
              }
            }}
            rows={3}
            placeholder="Ask a question about your uploaded document..."
            className="min-h-[84px] flex-1 resize-none rounded-[22px] border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none transition placeholder:text-mist focus:border-sky/50 focus:bg-white/[0.07]"
          />
          <button
            type="button"
            onClick={sendMessage}
            disabled={isLoading || !query.trim()}
            className="inline-flex min-w-36 items-center justify-center gap-3 rounded-[22px] bg-white px-5 py-3 font-semibold text-slate-950 transition hover:translate-y-[-1px] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLoading && <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-slate-900" />}
            Send
          </button>
        </div>
      </div>
    </section>
  );
}

export default Chat;

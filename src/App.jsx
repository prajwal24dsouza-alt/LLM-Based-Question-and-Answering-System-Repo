import { useState } from "react";
import Upload from "./components/Upload";
import Chat from "./components/Chat";

function App() {
  const [uploadSummary, setUploadSummary] = useState(null);
  const [activeDocument, setActiveDocument] = useState("");
  const statusLabel = uploadSummary
    ? `Indexed ${uploadSummary.fileName} with ${uploadSummary.chunksCreated} chunks.`
    : "Upload a PDF to build the knowledge base before asking questions.";

  return (
    <div className="min-h-screen bg-ink bg-mesh-glow font-body text-white">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 overflow-hidden rounded-[28px] border border-white/10 bg-white/5 shadow-halo backdrop-blur">
          <div className="flex flex-col gap-6 px-6 py-8 md:flex-row md:items-end md:justify-between md:px-8">
            <div className="max-w-2xl">
              <p className="mb-3 inline-flex rounded-full border border-sky/30 bg-sky/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.28em] text-sky">
                Retrieval-Augmented QA
              </p>
              <h1 className="font-display text-4xl leading-tight text-white sm:text-5xl">
                Search your documents and chat with grounded answers.
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-mist sm:text-base">
                Upload a PDF, let the backend index it, and ask natural-language questions in a focused chat workspace.
              </p>
            </div>

            <div className="max-w-sm rounded-3xl border border-white/10 bg-white/5 px-5 py-4 text-sm text-mist">
              <p className="font-display text-lg text-white">Knowledge Base Status</p>
              <p className="mt-2 leading-6">{statusLabel}</p>
              {activeDocument && (
                <p className="mt-3 truncate rounded-full bg-white/5 px-3 py-2 text-xs text-glow">
                  Active file: {activeDocument}
                </p>
              )}
            </div>
          </div>
        </header>

        <main className="grid flex-1 gap-6 lg:grid-cols-[380px_minmax(0,1fr)]">
          <Upload
            onUploadSuccess={(payload) => {
              setUploadSummary(payload);
              setActiveDocument(payload.fileName);
            }}
          />
          <Chat hasDocument={Boolean(uploadSummary)} activeDocument={activeDocument} />
        </main>
      </div>
    </div>
  );
}

export default App;

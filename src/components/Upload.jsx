import { useRef, useState } from "react";
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
});

function Upload({ onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef(null);

  const updateFile = (file) => {
    if (!file) {
      return;
    }

    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please upload a PDF file.");
      return;
    }

    setError("");
    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Choose a PDF before uploading.");
      return;
    }

    setIsUploading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await api.post("/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      onUploadSuccess({
        fileName: response.data.file_name,
        chunksCreated: response.data.details?.chunks_created ?? 0,
      });
    } catch (uploadError) {
      setError(uploadError.response?.data?.detail || "Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <section className="rounded-[28px] border border-white/10 bg-panel/75 p-5 shadow-halo backdrop-blur sm:p-6">
      <div className="mb-5">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-ember">File Upload</p>
        <h2 className="mt-2 font-display text-2xl text-white">Build the document index</h2>
        <p className="mt-2 text-sm leading-6 text-mist">
          Drop a PDF here, upload it to the backend, and prepare it for retrieval-augmented answering.
        </p>
      </div>

      <div
        onDragEnter={(event) => {
          event.preventDefault();
          setDragActive(true);
        }}
        onDragOver={(event) => {
          event.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setDragActive(false);
        }}
        onDrop={(event) => {
          event.preventDefault();
          setDragActive(false);
          updateFile(event.dataTransfer.files?.[0]);
        }}
        onClick={() => inputRef.current?.click()}
        className={`group relative flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-[24px] border border-dashed px-6 py-10 text-center transition ${
          dragActive
            ? "border-glow bg-glow/10"
            : "border-white/15 bg-white/[0.03] hover:border-sky/40 hover:bg-white/[0.05]"
        }`}
      >
        <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-white/10">
          <svg
            className="h-8 w-8 text-glow"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 16V4" />
            <path d="M7 9l5-5 5 5" />
            <path d="M20 16.7A4.7 4.7 0 0016.5 9h-1A7 7 0 103 16.3" />
            <path d="M16 16H8" />
          </svg>
        </div>

        <p className="font-display text-xl text-white">Drop your PDF here</p>
        <p className="mt-2 max-w-xs text-sm leading-6 text-mist">
          Or click to browse. The uploaded file will be sent to <span className="text-white">/upload</span>.
        </p>

        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={(event) => updateFile(event.target.files?.[0])}
        />
      </div>

      <div className="mt-5 rounded-2xl border border-white/10 bg-white/5 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-mist">Selected File</p>
        <p className="mt-2 truncate font-medium text-white">
          {selectedFile ? selectedFile.name : "No file selected yet"}
        </p>
      </div>

      {error && (
        <div className="mt-4 rounded-2xl border border-rose-400/25 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
          {error}
        </div>
      )}

      <button
        type="button"
        onClick={handleUpload}
        disabled={isUploading}
        className="mt-5 inline-flex w-full items-center justify-center gap-3 rounded-2xl bg-gradient-to-r from-ember to-sky px-4 py-3 font-semibold text-white transition hover:scale-[1.01] disabled:cursor-not-allowed disabled:opacity-70"
      >
        {isUploading && (
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
        )}
        {isUploading ? "Uploading and indexing..." : "Upload PDF"}
      </button>
    </section>
  );
}

export default Upload;

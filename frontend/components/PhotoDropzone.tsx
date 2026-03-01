"use client";
import { useCallback, useState } from "react";
import { Upload, X, ImagePlus } from "lucide-react";

interface PhotoDropzoneProps {
  onUpload: (files: File[]) => Promise<void>;
  maxFiles?: number;
  uploading?: boolean;
}

export function PhotoDropzone({
  onUpload,
  maxFiles = 5,
  uploading = false,
}: PhotoDropzoneProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [objectUrls, setObjectUrls] = useState<string[]>([]);

  const addFiles = (newFiles: FileList | null) => {
    if (!newFiles) return;
    const arr = Array.from(newFiles).filter((f) => f.type.startsWith("image/"));
    const combined = [...files, ...arr].slice(0, maxFiles);
    // Create object URLs for the new files
    const newUrls = arr.map((f) => URL.createObjectURL(f));
    setFiles(combined);
    setObjectUrls((prev) => [...prev, ...newUrls].slice(0, maxFiles));
  };

  const removeFile = (index: number) => {
    // Revoke the object URL to free memory
    URL.revokeObjectURL(objectUrls[index]);
    setFiles((prev) => prev.filter((_, i) => i !== index));
    setObjectUrls((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      addFiles(e.dataTransfer.files);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [files, maxFiles]
  );

  const handleUpload = async () => {
    await onUpload(files);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
          ${
            dragOver
              ? "border-red-400 bg-red-50"
              : "border-gray-300 hover:border-gray-400 bg-white"
          }`}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <input
          id="file-input"
          type="file"
          multiple
          accept="image/*"
          className="hidden"
          onChange={(e) => addFiles(e.target.files)}
        />
        <ImagePlus className="mx-auto h-10 w-10 text-gray-400 mb-3" />
        <p className="text-gray-600 font-medium">
          Drop photos here or click to browse
        </p>
        <p className="text-gray-400 text-sm mt-1">
          Up to {maxFiles} photos, images only
        </p>
        {files.length > 0 && (
          <p className="text-gray-500 text-sm mt-2 font-medium">
            {files.length} / {maxFiles} photo{files.length !== 1 ? "s" : ""}{" "}
            selected
          </p>
        )}
      </div>

      {files.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {files.map((file, i) => (
            <div
              key={i}
              className="relative bg-white rounded-lg border border-gray-200 overflow-hidden"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={objectUrls[i]}
                alt={file.name}
                className="w-full h-32 object-cover"
              />
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(i);
                }}
                className="absolute top-1 right-1 bg-black/60 text-white rounded-full p-0.5 hover:bg-black/80 transition-colors"
                aria-label={`Remove ${file.name}`}
              >
                <X size={14} />
              </button>
              <div className="p-1.5">
                <p className="text-xs text-gray-700 truncate font-medium">
                  {file.name}
                </p>
                <p className="text-xs text-gray-400">{formatFileSize(file.size)}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {files.length > 0 && (
        <button
          onClick={handleUpload}
          disabled={uploading}
          className="w-full py-2.5 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
        >
          <Upload size={18} />
          {uploading
            ? "Uploading..."
            : `Upload ${files.length} Photo${files.length > 1 ? "s" : ""}`}
        </button>
      )}
    </div>
  );
}

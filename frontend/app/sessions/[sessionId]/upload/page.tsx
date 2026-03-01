"use client";
import { useState, use } from "react";
import { useRouter } from "next/navigation";
import { PhotoDropzone } from "@/components/PhotoDropzone";
import { StepIndicator } from "@/components/StepIndicator";
import { uploadPhotos, confirmPhotos } from "@/lib/api";
import { usePhoto } from "@/lib/queries";
import type { Photo } from "@/types/api";

// PhotoStatusRow polls a single photo until done
function PhotoStatusRow({
  sessionId,
  photoId,
}: {
  sessionId: string;
  photoId: string;
}) {
  const { data: photo } = usePhoto(sessionId, photoId);
  if (!photo) return null;

  const icons: Record<string, string> = {
    pending: "⏳",
    processing: "🔄",
    done: "✅",
    failed: "❌",
  };

  const statusColors: Record<string, string> = {
    pending: "text-gray-500",
    processing: "text-blue-500",
    done: "text-green-600",
    failed: "text-red-600",
  };

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-base">{icons[photo.status] ?? "?"}</span>
      <span className="font-mono text-gray-600 text-xs flex-1 truncate">
        {photo.filename}
      </span>
      <span
        className={`capitalize text-xs font-medium ${
          statusColors[photo.status] ?? "text-gray-400"
        }`}
      >
        {photo.status}
      </span>
    </div>
  );
}

export default function UploadPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = use(params);
  const router = useRouter();
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const handleUpload = async (files: File[]) => {
    setUploading(true);
    try {
      const uploaded = await uploadPhotos(sessionId, files);
      setPhotos(uploaded);
    } finally {
      setUploading(false);
    }
  };

  const handleConfirm = async () => {
    setConfirming(true);
    try {
      await confirmPhotos(sessionId);
      router.push(`/sessions/${sessionId}/review`);
    } finally {
      setConfirming(false);
    }
  };

  return (
    <div className="space-y-8">
      <StepIndicator currentStep={1} />

      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Upload Your Lego Photos
        </h1>
        <p className="text-gray-500 mt-1">
          Spread your pieces flat on a light background and take clear photos.
          Upload up to 5 images.
        </p>
      </div>

      <PhotoDropzone onUpload={handleUpload} uploading={uploading} />

      {photos.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-2">
          <h2 className="font-semibold text-gray-700">Processing Photos</h2>
          <p className="text-xs text-gray-400 mb-3">
            AI is identifying your Lego pieces. This may take a moment.
          </p>
          <div className="space-y-2">
            {photos.map((p) => (
              <PhotoStatusRow key={p.id} sessionId={sessionId} photoId={p.id} />
            ))}
          </div>
          <div className="pt-2 border-t border-gray-100 mt-3">
            <button
              onClick={handleConfirm}
              disabled={confirming}
              className="w-full py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-60"
            >
              {confirming ? "Processing..." : "Confirm & Continue →"}
            </button>
            <p className="text-xs text-gray-400 text-center mt-2">
              You can continue even while photos are still processing.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

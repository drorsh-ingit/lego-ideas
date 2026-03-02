"use client";
import { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";
import { getPartInfo } from "@/lib/api";
import type { BomEntry, Color } from "@/types/api";

interface BomTableProps {
  entries: BomEntry[];
  colors: Color[];
  onUpdate: (
    entryId: string,
    data: { quantity?: number; color_id?: number | null }
  ) => void;
  onDelete: (entryId: string) => void;
}

function PartImage({ partNum }: { partNum: string }) {
  const [imgUrl, setImgUrl] = useState<string | null>(null);

  useEffect(() => {
    getPartInfo(partNum).then((info) => setImgUrl(info.img_url)).catch(() => {});
  }, [partNum]);

  if (!imgUrl) return <div className="w-12 h-12 bg-gray-100 rounded" />;
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={imgUrl}
      alt={partNum}
      className="w-12 h-12 object-contain rounded bg-gray-50"
      onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
    />
  );
}

export function BomTable({ entries, colors, onUpdate, onDelete }: BomTableProps) {
  if (entries.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
        <p className="text-gray-400 text-lg">No pieces identified yet.</p>
        <p className="text-gray-300 text-sm mt-1">
          Upload photos or add pieces manually below.
        </p>
      </div>
    );
  }

  const getColorById = (colorId: number | null): Color | undefined => {
    if (colorId === null) return undefined;
    return colors.find((c) => c.id === colorId);
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
            <tr>
              <th className="px-4 py-3" />
              <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">
                Part #
              </th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">
                Color
              </th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">
                Qty
              </th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">
                Source
              </th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">
                Confidence
              </th>
              <th className="text-right px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {entries.map((entry) => {
              const selectedColor = getColorById(entry.color_id);
              return (
                <tr key={entry.id} className="hover:bg-gray-50 transition-colors">
                  {/* Part image */}
                  <td className="px-4 py-3">
                    <PartImage partNum={entry.part_num} />
                  </td>

                  {/* Part number */}
                  <td className="px-4 py-3">
                    <span className="font-mono text-gray-800 text-xs bg-gray-100 px-2 py-1 rounded">
                      {entry.part_num}
                    </span>
                  </td>

                  {/* Color selector */}
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {selectedColor && (
                        <div
                          className="w-4 h-4 rounded-full border border-gray-300 flex-shrink-0"
                          style={{ backgroundColor: `#${selectedColor.rgb}` }}
                          title={selectedColor.name}
                        />
                      )}
                      <select
                        value={entry.color_id ?? ""}
                        onChange={(e) => {
                          const val = e.target.value;
                          onUpdate(entry.id, {
                            color_id: val === "" ? null : Number(val),
                          });
                        }}
                        className="text-sm border border-gray-200 rounded px-2 py-1 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-red-300 max-w-[160px]"
                      >
                        <option value="">Unknown</option>
                        {colors.map((color) => (
                          <option key={color.id} value={color.id}>
                            {color.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </td>

                  {/* Quantity */}
                  <td className="px-4 py-3">
                    <input
                      type="number"
                      min="1"
                      value={entry.quantity}
                      onChange={(e) => {
                        const val = parseInt(e.target.value, 10);
                        if (!isNaN(val) && val >= 1) {
                          onUpdate(entry.id, { quantity: val });
                        }
                      }}
                      className="w-16 text-sm border border-gray-200 rounded px-2 py-1 text-center focus:outline-none focus:ring-1 focus:ring-red-300"
                    />
                  </td>

                  {/* Source badge */}
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        entry.source === "photo"
                          ? "bg-blue-100 text-blue-700"
                          : "bg-green-100 text-green-700"
                      }`}
                    >
                      {entry.source}
                    </span>
                  </td>

                  {/* Confidence */}
                  <td className="px-4 py-3">
                    {entry.confidence !== null ? (
                      <span
                        className={`text-xs font-medium ${
                          entry.confidence >= 0.8
                            ? "text-green-600"
                            : entry.confidence >= 0.5
                            ? "text-yellow-600"
                            : "text-red-600"
                        }`}
                      >
                        {Math.round(entry.confidence * 100)}%
                      </span>
                    ) : (
                      <span className="text-gray-300 text-xs">—</span>
                    )}
                  </td>

                  {/* Delete */}
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => onDelete(entry.id)}
                      className="text-gray-400 hover:text-red-500 transition-colors p-1 rounded hover:bg-red-50"
                      aria-label={`Delete part ${entry.part_num}`}
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="px-4 py-2 bg-gray-50 border-t border-gray-100 text-xs text-gray-400">
        {entries.length} piece{entries.length !== 1 ? "s" : ""} total
      </div>
    </div>
  );
}

"use client";
import type { MissingPart, Color } from "@/types/api";

interface MissingPiecesListProps {
  missing: MissingPart[];
  colors: Color[];
}

export function MissingPiecesList({ missing, colors }: MissingPiecesListProps) {
  if (missing.length === 0) {
    return (
      <p className="text-sm text-green-600 font-medium py-2">
        You have all the pieces for this set!
      </p>
    );
  }

  const getColorById = (colorId: number | null): Color | undefined => {
    if (colorId === null) return undefined;
    return colors.find((c) => c.id === colorId);
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs font-semibold text-gray-500 border-b border-gray-100">
            <th className="pb-2 pr-4 whitespace-nowrap">Part #</th>
            <th className="pb-2 pr-4 whitespace-nowrap">Color</th>
            <th className="pb-2 pr-4 text-center whitespace-nowrap">Need</th>
            <th className="pb-2 pr-4 text-center whitespace-nowrap">Have</th>
            <th className="pb-2 text-center whitespace-nowrap">Short</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {missing.map((part, index) => {
            const color = getColorById(part.color_id);
            const short = part.needed - part.have;

            return (
              <tr key={`${part.part_num}-${part.color_id}-${index}`} className="hover:bg-gray-50">
                {/* Part number */}
                <td className="py-1.5 pr-4">
                  <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded text-gray-700">
                    {part.part_num}
                  </span>
                </td>

                {/* Color */}
                <td className="py-1.5 pr-4">
                  <div className="flex items-center gap-1.5">
                    {color ? (
                      <>
                        <div
                          className="w-3 h-3 rounded-full border border-gray-300 flex-shrink-0"
                          style={{ backgroundColor: `#${color.rgb}` }}
                        />
                        <span className="text-xs text-gray-600 whitespace-nowrap">
                          {color.name}
                        </span>
                      </>
                    ) : (
                      <span className="text-xs text-gray-400 italic">Any color</span>
                    )}
                  </div>
                </td>

                {/* Need */}
                <td className="py-1.5 pr-4 text-center">
                  <span className="text-xs font-medium text-gray-700">{part.needed}</span>
                </td>

                {/* Have */}
                <td className="py-1.5 pr-4 text-center">
                  <span className="text-xs font-medium text-gray-700">{part.have}</span>
                </td>

                {/* Short */}
                <td className="py-1.5 text-center">
                  <span className="text-xs font-bold text-red-600">-{short}</span>
                </td>
              </tr>
            );
          })}
        </tbody>
        <tfoot>
          <tr className="border-t border-gray-100">
            <td colSpan={5} className="pt-2 text-xs text-gray-400">
              {missing.length} missing part type{missing.length !== 1 ? "s" : ""}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

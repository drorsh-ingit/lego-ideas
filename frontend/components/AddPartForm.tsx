"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { Plus } from "lucide-react";
import { searchParts } from "@/lib/api";
import type { Color, Part } from "@/types/api";

interface AddPartFormProps {
  sessionId: string;
  colors: Color[];
  onAdd: (data: {
    part_num: string;
    color_id?: number | null;
    quantity: number;
  }) => void;
}

export function AddPartForm({ sessionId: _sessionId, colors, onAdd }: AddPartFormProps) {
  const [partNum, setPartNum] = useState("");
  const [colorId, setColorId] = useState<number | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [suggestions, setSuggestions] = useState<Part[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  const fetchSuggestions = useCallback(async (query: string) => {
    if (query.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    setLoadingSuggestions(true);
    try {
      const parts = await searchParts(query);
      setSuggestions(parts.slice(0, 8));
      setShowSuggestions(parts.length > 0);
    } catch {
      setSuggestions([]);
      setShowSuggestions(false);
    } finally {
      setLoadingSuggestions(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchSuggestions(partNum);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [partNum, fetchSuggestions]);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelectSuggestion = (part: Part) => {
    setPartNum(part.part_num);
    setSuggestions([]);
    setShowSuggestions(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!partNum.trim() || quantity < 1) return;
    setSubmitting(true);
    try {
      await onAdd({
        part_num: partNum.trim(),
        color_id: colorId,
        quantity,
      });
      // Reset form
      setPartNum("");
      setColorId(null);
      setQuantity(1);
      setSuggestions([]);
      setShowSuggestions(false);
    } finally {
      setSubmitting(false);
    }
  };

  const selectedColor = colors.find((c) => c.id === colorId);

  return (
    <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
      {/* Part number input with autocomplete */}
      <div className="relative flex-1">
        <input
          ref={inputRef}
          type="text"
          value={partNum}
          onChange={(e) => setPartNum(e.target.value)}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          placeholder="Part number (e.g. 3001)"
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-300 focus:border-transparent"
          autoComplete="off"
        />
        {loadingSuggestions && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
          </div>
        )}

        {/* Suggestions dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div
            ref={suggestionsRef}
            className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto"
          >
            {suggestions.map((part) => (
              <button
                key={part.part_num}
                type="button"
                onClick={() => handleSelectSuggestion(part)}
                className="w-full text-left px-3 py-2 hover:bg-gray-50 transition-colors"
              >
                <span className="font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded text-gray-700 mr-2">
                  {part.part_num}
                </span>
                <span className="text-sm text-gray-600 truncate">{part.name}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Color select */}
      <div className="flex items-center gap-2 sm:w-48">
        {selectedColor && (
          <div
            className="w-5 h-5 rounded-full border border-gray-300 flex-shrink-0"
            style={{ backgroundColor: `#${selectedColor.rgb}` }}
          />
        )}
        <select
          value={colorId ?? ""}
          onChange={(e) => {
            const val = e.target.value;
            setColorId(val === "" ? null : Number(val));
          }}
          className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-300 focus:border-transparent bg-white"
        >
          <option value="">Any color</option>
          {colors.map((color) => (
            <option key={color.id} value={color.id}>
              {color.name}
            </option>
          ))}
        </select>
      </div>

      {/* Quantity input */}
      <input
        type="number"
        min="1"
        value={quantity}
        onChange={(e) => {
          const val = parseInt(e.target.value, 10);
          if (!isNaN(val) && val >= 1) setQuantity(val);
        }}
        className="w-20 border border-gray-200 rounded-lg px-3 py-2 text-sm text-center focus:outline-none focus:ring-2 focus:ring-red-300 focus:border-transparent"
        placeholder="Qty"
      />

      {/* Submit button */}
      <button
        type="submit"
        disabled={submitting || !partNum.trim()}
        className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg text-sm transition-colors disabled:opacity-60 whitespace-nowrap"
      >
        <Plus size={16} />
        {submitting ? "Adding..." : "Add Part"}
      </button>
    </form>
  );
}

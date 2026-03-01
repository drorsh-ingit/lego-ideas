"use client";
import { Check } from "lucide-react";

interface StepIndicatorProps {
  currentStep: 1 | 2 | 3;
}

const steps = [
  { number: 1, label: "Upload" },
  { number: 2, label: "Review" },
  { number: 3, label: "Results" },
];

export function StepIndicator({ currentStep }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center w-full">
      {steps.map((step, index) => {
        const isCompleted = step.number < currentStep;
        const isCurrent = step.number === currentStep;
        const isFuture = step.number > currentStep;

        return (
          <div key={step.number} className="flex items-center">
            {/* Step circle + label */}
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-semibold text-sm transition-colors
                  ${isCompleted
                    ? "bg-red-600 text-white"
                    : isCurrent
                    ? "bg-red-600 text-white ring-4 ring-red-100"
                    : "bg-white border-2 border-gray-300 text-gray-400"
                  }`}
              >
                {isCompleted ? (
                  <Check size={16} strokeWidth={3} />
                ) : (
                  <span>{step.number}</span>
                )}
              </div>
              <span
                className={`text-xs font-medium ${
                  isFuture ? "text-gray-400" : "text-gray-700"
                }`}
              >
                {step.label}
              </span>
            </div>

            {/* Connector line between steps */}
            {index < steps.length - 1 && (
              <div
                className={`h-0.5 w-16 sm:w-24 mx-2 mb-5 transition-colors ${
                  step.number < currentStep ? "bg-red-600" : "bg-gray-200"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

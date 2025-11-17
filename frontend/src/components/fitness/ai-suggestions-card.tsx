"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  AlertCircle,
  CheckCircle,
  Info,
  Lightbulb,
  TrendingUp,
  X,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// Priority color mapping
const PRIORITY_CONFIG = {
  high: {
    color: "bg-red-100 text-red-800 border-red-300",
    icon: AlertCircle,
    iconColor: "text-red-600",
  },
  medium: {
    color: "bg-yellow-100 text-yellow-800 border-yellow-300",
    icon: Info,
    iconColor: "text-yellow-600",
  },
  low: {
    color: "bg-blue-100 text-blue-800 border-blue-300",
    icon: Lightbulb,
    iconColor: "text-blue-600",
  },
};

// Category icon mapping
const CATEGORY_ICONS: Record<string, any> = {
  "Progressive Overload": TrendingUp,
  "Schedule Optimization": AlertCircle,
  "Workout Optimization": CheckCircle,
  "Nutrition Planning": CheckCircle,
  "Flexibility & Options": Lightbulb,
  "Goal Expansion": TrendingUp,
};

interface Recommendation {
  category: string;
  priority: "high" | "medium" | "low";
  title: string;
  description: string;
  action_items: string[];
  expected_impact: string;
}

interface SuggestionsData {
  user_id: string;
  fitness_plan_id: string;
  analysis_summary: {
    overall_adherence: number;
    workout_adherence: number;
    meal_adherence: number;
  };
  recommendations: Recommendation[];
  generated_at: string;
}

interface AISuggestionsCardProps {
  planId: string;
  accessToken: string;
  onApplySuggestion?: (recommendation: Recommendation) => void;
}

export function AISuggestionsCard({
  planId,
  accessToken,
  onApplySuggestion,
}: AISuggestionsCardProps) {
  const [suggestions, setSuggestions] = useState<SuggestionsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dismissedIds, setDismissedIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    fetchSuggestions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [planId]);

  const fetchSuggestions = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Call the backend endpoint to get improvement recommendations
      const res = await fetch(`${API_URL}/fitness-plans/${planId}/suggestions`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to fetch suggestions");
      }

      const data = await res.json();
      // Handle both {data: {...}} and direct {...} response formats
      const responseData = data.data || data;
      setSuggestions(responseData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load suggestions");
      console.error("Error fetching suggestions:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDismiss = (index: number) => {
    setDismissedIds((prev) => new Set(prev).add(index));
  };

  const handleApply = (recommendation: Recommendation) => {
    if (onApplySuggestion) {
      onApplySuggestion(recommendation);
    } else {
      // Default behavior: log to console
      console.log("Apply suggestion:", recommendation);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-blue-600" />
            AI Recommendations
          </CardTitle>
          <CardDescription>Loading personalized suggestions...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-blue-600" />
            AI Recommendations
          </CardTitle>
          <CardDescription className="text-red-600">{error}</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={fetchSuggestions} variant="outline" size="sm">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  // No suggestions state
  if (!suggestions || suggestions.recommendations.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-blue-600" />
            AI Recommendations
          </CardTitle>
          <CardDescription>
            No recommendations available yet. Keep logging your progress!
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Filter out dismissed recommendations
  const visibleRecommendations = suggestions.recommendations.filter(
    (_, index) => !dismissedIds.has(index)
  );

  if (visibleRecommendations.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-blue-600" />
            AI Recommendations
          </CardTitle>
          <CardDescription>
            All suggestions dismissed. Keep up the great work!
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-blue-600" />
          AI Recommendations
        </CardTitle>
        <CardDescription>
          Based on your {suggestions.analysis_summary.overall_adherence.toFixed(0)}%
          adherence rate
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {visibleRecommendations.map((recommendation, index) => {
          const priorityConfig = PRIORITY_CONFIG[recommendation.priority];
          const CategoryIcon =
            CATEGORY_ICONS[recommendation.category] || Lightbulb;

          return (
            <div
              key={index}
              className="relative rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
            >
              {/* Dismiss button */}
              <button
                onClick={() => handleDismiss(index)}
                className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
                aria-label="Dismiss suggestion"
              >
                <X className="h-4 w-4" />
              </button>

              {/* Header with priority and category */}
              <div className="mb-3 flex items-start gap-3">
                <div className={`rounded-full p-2 ${priorityConfig.iconColor}`}>
                  <CategoryIcon className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <div className="mb-1 flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className={`${priorityConfig.color} text-xs font-semibold uppercase`}
                    >
                      {recommendation.priority}
                    </Badge>
                    <span className="text-xs font-medium text-gray-500">
                      {recommendation.category}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {recommendation.title}
                  </h3>
                </div>
              </div>

              {/* Description */}
              <p className="mb-3 text-sm text-gray-600">
                {recommendation.description}
              </p>

              {/* Action items */}
              <div className="mb-3">
                <p className="mb-2 text-xs font-semibold uppercase text-gray-500">
                  Action Items
                </p>
                <ul className="space-y-1">
                  {recommendation.action_items.map((item, itemIndex) => (
                    <li
                      key={itemIndex}
                      className="flex items-start gap-2 text-sm text-gray-700"
                    >
                      <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-green-600" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Expected impact */}
              <div className="mb-4 rounded bg-blue-50 p-2">
                <p className="text-xs text-gray-600">
                  <span className="font-semibold">Expected Impact: </span>
                  {recommendation.expected_impact}
                </p>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <Button
                  onClick={() => handleApply(recommendation)}
                  size="sm"
                  className="flex-1"
                >
                  Apply Suggestion
                </Button>
                <Button
                  onClick={() => handleDismiss(index)}
                  size="sm"
                  variant="outline"
                  className="flex-1"
                >
                  Dismiss
                </Button>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

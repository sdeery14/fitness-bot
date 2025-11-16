"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar, Target, TrendingUp } from "lucide-react";

interface FitnessPlan {
  id: string;
  goal: string;
  duration_weeks: number;
  status: string;
  created_at: string;
  completed_at?: string;
  requirements: {
    fitness_level?: string;
    equipment_access?: string[];
    dietary_restrictions?: string[];
    workout_frequency?: number;
  };
}

interface PlanOverviewProps {
  plan: FitnessPlan;
}

export function PlanOverview({ plan }: PlanOverviewProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800 border-green-200";
      case "generating":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "failed":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-2xl">{plan.goal}</CardTitle>
            <CardDescription className="mt-2">
              Created {formatDate(plan.created_at)}
            </CardDescription>
          </div>
          <Badge className={getStatusColor(plan.status)} variant="outline">
            {plan.status.charAt(0).toUpperCase() + plan.status.slice(1)}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Duration */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Calendar className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="text-sm font-medium">Duration</p>
            <p className="text-2xl font-bold">{plan.duration_weeks} weeks</p>
          </div>
        </div>

        {/* Requirements Grid */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Fitness Level */}
          {plan.requirements.fitness_level && (
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50">
                <TrendingUp className="h-5 w-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-700">Fitness Level</p>
                <p className="text-sm text-gray-600 capitalize">
                  {plan.requirements.fitness_level}
                </p>
              </div>
            </div>
          )}

          {/* Workout Frequency */}
          {plan.requirements.workout_frequency && (
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-50">
                <Target className="h-5 w-5 text-purple-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-700">Workout Frequency</p>
                <p className="text-sm text-gray-600">
                  {plan.requirements.workout_frequency} days per week
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Equipment */}
        {plan.requirements.equipment_access && plan.requirements.equipment_access.length > 0 && (
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Equipment Available</p>
            <div className="flex flex-wrap gap-2">
              {plan.requirements.equipment_access.map((equipment) => (
                <Badge key={equipment} variant="secondary">
                  {equipment}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Dietary Restrictions */}
        {plan.requirements.dietary_restrictions && plan.requirements.dietary_restrictions.length > 0 && (
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Dietary Preferences</p>
            <div className="flex flex-wrap gap-2">
              {plan.requirements.dietary_restrictions.map((restriction) => (
                <Badge key={restriction} variant="secondary">
                  {restriction}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

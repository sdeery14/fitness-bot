"use client";

import { useState, useEffect } from "react";
import { ChevronDown, ChevronUp, Calendar, Dumbbell, Utensils, Target } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface Phase {
  phase_number: number;
  phase_name: string;
  duration_weeks: number;
  description: string;
  workouts: any[];
  meals: any[];
}

interface PlanData {
  duration_weeks: number;
  phases: Phase[];
  daily_calorie_target?: number;
  workout_frequency?: number;
}

interface PlanMessageCardProps {
  planId: string;
}

export function PlanMessageCard({ planId }: PlanMessageCardProps) {
  const [planData, setPlanData] = useState<PlanData | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [expandedPhase, setExpandedPhase] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadPlanData = async () => {
      try {
        const token = localStorage.getItem("access_token");
        const res = await fetch(`${API_URL}/plans/${planId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          throw new Error("Failed to load plan data");
        }

        const data = await res.json();
        const responseData = data.data || data;
        
        // Parse plan_snapshot if it's a string
        const planSnapshot = typeof responseData.plan_snapshot === "string"
          ? JSON.parse(responseData.plan_snapshot)
          : responseData.plan_snapshot;

        setPlanData(planSnapshot);
      } catch (err) {
        console.error("Error loading plan:", err);
        setError("Failed to load plan details");
      } finally {
        setIsLoading(false);
      }
    };

    loadPlanData();
  }, [planId]);

  if (isLoading) {
    return (
      <Card className="my-4 border-2 border-blue-200 bg-blue-50">
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>
            <span className="ml-2 text-gray-600">Loading plan...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !planData) {
    return (
      <Card className="my-4 border-2 border-red-200 bg-red-50">
        <CardContent className="p-6">
          <p className="text-red-600">{error || "Failed to load plan"}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="my-4 border-2 border-blue-500 bg-gradient-to-br from-blue-50 to-indigo-50">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-blue-900">
          <Target className="h-6 w-6" />
          🎯 Your Fitness Plan
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overview Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-white rounded-lg p-3 shadow-sm">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Calendar className="h-4 w-4" />
              Duration
            </div>
            <div className="text-xl font-bold text-gray-900">{planData.duration_weeks} weeks</div>
          </div>
          <div className="bg-white rounded-lg p-3 shadow-sm">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Target className="h-4 w-4" />
              Phases
            </div>
            <div className="text-xl font-bold text-gray-900">{planData.phases.length}</div>
          </div>
          {planData.workout_frequency && (
            <div className="bg-white rounded-lg p-3 shadow-sm">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Dumbbell className="h-4 w-4" />
                Workouts/Week
              </div>
              <div className="text-xl font-bold text-gray-900">{planData.workout_frequency}</div>
            </div>
          )}
          {planData.daily_calorie_target && (
            <div className="bg-white rounded-lg p-3 shadow-sm">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Utensils className="h-4 w-4" />
                Calories/Day
              </div>
              <div className="text-xl font-bold text-gray-900">{planData.daily_calorie_target.toLocaleString()}</div>
            </div>
          )}
        </div>

        {/* Phase Summary */}
        {!isExpanded && (
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <h4 className="font-semibold text-gray-900 mb-2">Phases:</h4>
            <div className="space-y-1">
              {planData.phases.map((phase) => (
                <div key={phase.phase_number} className="text-sm text-gray-700">
                  <span className="font-medium">Phase {phase.phase_number}:</span> {phase.phase_name} ({phase.duration_weeks} weeks)
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Expanded Phase Details */}
        {isExpanded && (
          <div className="space-y-3">
            {planData.phases.map((phase) => (
              <div key={phase.phase_number} className="bg-white rounded-lg shadow-sm overflow-hidden">
                <button
                  onClick={() => setExpandedPhase(expandedPhase === phase.phase_number ? null : phase.phase_number)}
                  className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <div className="text-left">
                    <div className="font-semibold text-gray-900">
                      Phase {phase.phase_number}: {phase.phase_name}
                    </div>
                    <div className="text-sm text-gray-600">
                      {phase.duration_weeks} weeks • {phase.workouts.length} workouts • {phase.meals.length} meal plans
                    </div>
                  </div>
                  {expandedPhase === phase.phase_number ? (
                    <ChevronUp className="h-5 w-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-gray-400" />
                  )}
                </button>

                {expandedPhase === phase.phase_number && (
                  <div className="p-4 pt-0 space-y-4 border-t">
                    <p className="text-sm text-gray-700">{phase.description}</p>

                    {/* Workouts */}
                    <div>
                      <h5 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                        <Dumbbell className="h-4 w-4" />
                        Workouts
                      </h5>
                      <div className="space-y-2">
                        {phase.workouts.map((workout, idx) => (
                          <div key={idx} className="bg-gray-50 rounded p-3 text-sm">
                            <div className="font-medium text-gray-900">{workout.workout_name}</div>
                            <div className="text-gray-600">{workout.exercises?.length || 0} exercises</div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Meals */}
                    <div>
                      <h5 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                        <Utensils className="h-4 w-4" />
                        Meal Plans
                      </h5>
                      <div className="space-y-2">
                        {phase.meals.map((meal, idx) => (
                          <div key={idx} className="bg-gray-50 rounded p-3 text-sm">
                            <div className="font-medium text-gray-900">Day {meal.day_number}</div>
                            <div className="text-gray-600">{meal.daily_meals?.length || 0} meals • {meal.total_calories} cal</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 pt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex-1"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-4 w-4 mr-1" />
                Show Less
              </>
            ) : (
              <>
                <ChevronDown className="h-4 w-4 mr-1" />
                Show Details
              </>
            )}
          </Button>
          <Link href={`/dashboard/plans/${planId}`} className="flex-1">
            <Button size="sm" className="w-full">
              View Full Plan →
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

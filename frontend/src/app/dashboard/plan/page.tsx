"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PhaseTimeline } from "@/components/fitness/phase-timeline";
import { MilestoneCelebration } from "@/components/fitness/milestone-celebration";
import {
  ArrowLeft,
  Calendar,
  Target,
  TrendingUp,
  Clock,
  AlertCircle,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface Phase {
  id: string;
  phase_number: number;
  name: string;
  objectives: string[];
  start_date: string;
  end_date: string;
  phase_details: any;
}

interface FitnessPlan {
  id: string;
  user_id: string;
  goal_description: string;
  goal_type: string;
  duration_weeks: number;
  start_date: string;
  target_end_date: string;
  current_status: string;
  plan_snapshot: any;
  created_at: string;
  updated_at: string;
}

interface PhaseStatus {
  has_phases: boolean;
  current_phase: {
    id: string;
    phase_number: number;
    name: string;
    objectives: string[];
    start_date: string;
    end_date: string;
    days_remaining: number;
  } | null;
  next_phase: {
    id: string;
    phase_number: number;
    name: string;
    objectives: string[];
    start_date: string;
    end_date: string;
  } | null;
  is_complete: boolean;
  should_transition: boolean;
  all_phases_complete?: boolean;
}

export default function PlanPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [plan, setPlan] = useState<FitnessPlan | null>(null);
  const [phases, setPhases] = useState<Phase[]>([]);
  const [phaseStatus, setPhaseStatus] = useState<PhaseStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showMilestone, setShowMilestone] = useState(false);
  const [currentMilestone, setCurrentMilestone] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
    } else {
      setAccessToken(token);
      fetchPlanData(token);
    }
  }, [router]);

  const fetchPlanData = async (token: string) => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch active plan
      const planRes = await fetch(`${API_URL}/fitness-plans/active`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!planRes.ok) {
        throw new Error("No active fitness plan found");
      }

      const planData = await planRes.json();
      const activePlan = planData.data || planData;
      setPlan(activePlan);

      // Extract phases from plan snapshot if available
      if (activePlan.plan_snapshot && activePlan.plan_snapshot.phases) {
        setPhases(activePlan.plan_snapshot.phases);
      }

      // Fetch phase status (this would be a new endpoint)
      // For now, we'll derive it from the plan data
      if (activePlan.plan_snapshot && activePlan.plan_snapshot.phases) {
        const today = new Date();
        const currentPhase = activePlan.plan_snapshot.phases.find((p: Phase) => {
          const start = new Date(p.start_date);
          const end = new Date(p.end_date);
          return start <= today && today <= end;
        });

        if (currentPhase) {
          const endDate = new Date(currentPhase.end_date);
          const daysRemaining = Math.ceil(
            (endDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
          );

          const currentIndex = activePlan.plan_snapshot.phases.findIndex(
            (p: Phase) => p.id === currentPhase.id
          );
          const nextPhase =
            currentIndex < activePlan.plan_snapshot.phases.length - 1
              ? activePlan.plan_snapshot.phases[currentIndex + 1]
              : null;

          setPhaseStatus({
            has_phases: true,
            current_phase: {
              ...currentPhase,
              days_remaining: daysRemaining,
            },
            next_phase: nextPhase,
            is_complete: daysRemaining <= 2,
            should_transition: daysRemaining <= 2 && nextPhase !== null,
          });
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load plan data");
      console.error("Error fetching plan:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent"></div>
          <p className="mt-4 text-gray-600">Loading your fitness plan...</p>
        </div>
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center max-w-md">
          <AlertCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <p className="text-red-600 mb-4">{error || "No active plan found"}</p>
          <Button onClick={() => router.push("/dashboard")}>
            Go to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/dashboard")}
                className="text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Dashboard
              </Button>
              <div className="h-6 w-px bg-gray-300"></div>
              <h1 className="text-xl font-semibold text-gray-900">
                Fitness Plan
              </h1>
            </div>
            <Badge
              variant={plan.current_status === "active" ? "default" : "secondary"}
            >
              {plan.current_status}
            </Badge>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="space-y-6">
          {/* Plan Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-blue-600" />
                Plan Overview
              </CardTitle>
              <CardDescription>
                Your personalized fitness journey
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {plan.goal_description}
                </h3>
                <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    <span>Started: {formatDate(plan.start_date)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Target className="h-4 w-4" />
                    <span>Target: {formatDate(plan.target_end_date)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    <span>Duration: {plan.duration_weeks} weeks</span>
                  </div>
                </div>
              </div>

              {phaseStatus && phaseStatus.current_phase && (
                <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-blue-900">
                      Current Phase: {phaseStatus.current_phase.name}
                    </h4>
                    <Badge variant="outline" className="bg-white">
                      Phase {phaseStatus.current_phase.phase_number}
                    </Badge>
                  </div>
                  <p className="text-sm text-blue-700 mb-3">
                    {phaseStatus.current_phase.days_remaining} days remaining
                  </p>
                  <div>
                    <p className="text-xs font-semibold text-blue-900 mb-2 uppercase">
                      Phase Objectives:
                    </p>
                    <ul className="space-y-1">
                      {phaseStatus.current_phase.objectives.map((obj: string, idx: number) => (
                        <li key={idx} className="text-sm text-blue-800 flex items-start gap-2">
                          <TrendingUp className="h-4 w-4 flex-shrink-0 mt-0.5" />
                          <span>{obj}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Phase Timeline */}
          {phases.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Phase Timeline</CardTitle>
                <CardDescription>
                  Track your progress through each phase of your fitness journey
                </CardDescription>
              </CardHeader>
              <CardContent>
                <PhaseTimeline
                  phases={phases}
                  currentPhaseNumber={phaseStatus?.current_phase?.phase_number || 1}
                />
              </CardContent>
            </Card>
          )}

          {/* Plan Details */}
          {plan.plan_snapshot && (
            <Card>
              <CardHeader>
                <CardTitle>Plan Details</CardTitle>
                <CardDescription>
                  Generated on {formatDate(plan.created_at)}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {plan.plan_snapshot.workouts && plan.plan_snapshot.workouts.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">
                        Workouts ({plan.plan_snapshot.workouts.length})
                      </h4>
                      <div className="grid gap-2">
                        {plan.plan_snapshot.workouts.slice(0, 3).map((workout: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                          >
                            <p className="font-medium text-gray-900">{workout.name}</p>
                            <p className="text-sm text-gray-600">
                              {workout.type} • {workout.duration_minutes || 45} minutes
                            </p>
                          </div>
                        ))}
                        {plan.plan_snapshot.workouts.length > 3 && (
                          <p className="text-sm text-gray-500 text-center">
                            +{plan.plan_snapshot.workouts.length - 3} more workouts
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {plan.plan_snapshot.meals && plan.plan_snapshot.meals.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">
                        Meals ({plan.plan_snapshot.meals.length})
                      </h4>
                      <div className="grid gap-2">
                        {plan.plan_snapshot.meals.slice(0, 3).map((meal: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                          >
                            <p className="font-medium text-gray-900">{meal.name}</p>
                            <p className="text-sm text-gray-600">
                              {meal.time} • {meal.calories || 0} calories
                            </p>
                          </div>
                        ))}
                        {plan.plan_snapshot.meals.length > 3 && (
                          <p className="text-sm text-gray-500 text-center">
                            +{plan.plan_snapshot.meals.length - 3} more meals
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Milestone Celebration Dialog */}
      <MilestoneCelebration
        milestone={currentMilestone}
        open={showMilestone}
        onClose={() => setShowMilestone(false)}
      />
    </div>
  );
}
